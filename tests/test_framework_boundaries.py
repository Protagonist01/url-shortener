"""Synthetic library regressions; these do not add an application upload route."""
import asyncio
import io
import os
from pathlib import Path
from tempfile import SpooledTemporaryFile, TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

import python_multipart.multipart as multipart
from python_multipart.exceptions import MultipartParseError
from starlette.applications import Starlette
from starlette.datastructures import URL, UploadFile
from starlette.endpoints import HTTPEndpoint
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, PlainTextResponse, MalformedRangeHeader
from starlette.routing import Route
from starlette.staticfiles import StaticFiles
from starlette.testclient import TestClient


def scope(**values):
    return {"type": "http", "method": "GET", "path": "/private", "scheme": "http",
            "query_string": b"", "server": ("trusted.invalid", 80),
            "headers": [(b"host", b"trusted.invalid")], **values}


async def form(body, content_type="application/x-www-form-urlencoded", chunk_size=7, **limits):
    chunks = [body[n:n + chunk_size] for n in range(0, len(body), chunk_size)] or [b""]
    async def receive():
        chunk = chunks.pop(0)
        return {"type": "http.request", "body": chunk, "more_body": bool(chunks)}
    request = Request(scope(app=object(), headers=[(b"content-type", content_type.encode())]), receive)
    return await request.form(**limits)


class FrameworkBoundaries(unittest.TestCase):
    def test_host_cannot_prepend_path_or_override_authority(self):
        for host in (b"trusted.invalid/public", b"trusted.invalid@evil.invalid", b"evil.invalid\\share"):
            with self.subTest(host=host):
                value = URL(scope=scope(headers=[(b"host", host)]))
                self.assertEqual(value.path, "/private")
                self.assertEqual(value.hostname, "trusted.invalid")
        self.assertEqual(URL(scope=scope()).hostname, "trusted.invalid")

    def test_non_slash_path_cannot_move_authority(self):
        value = URL(scope=scope(path="@evil.invalid"))
        self.assertEqual(value.hostname, "trusted.invalid")
        self.assertEqual(value.path, "/@evil.invalid")

    def test_endpoint_internal_helper_is_not_a_custom_http_method(self):
        called = []
        class Endpoint(HTTPEndpoint):
            async def get(self, request):
                return PlainTextResponse("public")
            async def internal(self, request):
                called.append(True)
                return PlainTextResponse("private")
        with TestClient(Starlette(routes=[Route("/", Endpoint)])) as client:
            self.assertEqual(client.get("/").text, "public")
            self.assertEqual(client.request("INTERNAL", "/").status_code, 405)
        self.assertEqual(called, [])

    def test_absolute_unc_rejected_before_filesystem_resolution(self):
        with TemporaryDirectory() as directory:
            static = StaticFiles(directory=directory)
            # Never contact an external SMB host, including on Windows.
            with patch("starlette.staticfiles.os.path.realpath", side_effect=AssertionError("filesystem touched")):
                for path in ("\\\\synthetic.invalid\\share", "/absolute", "\\absolute"):
                    self.assertEqual(static.lookup_path(path), ("", None))
            sentinel = Path(directory) / "inside.txt"
            sentinel.write_text("ordinary")
            self.assertEqual(Path(static.lookup_path("inside.txt")[0]), sentinel)
            self.assertEqual(static.lookup_path("../outside.txt"), ("", None))

    def test_ranges_are_merged_and_invalid_numeric_work_is_bounded(self):
        self.assertEqual(FileResponse._parse_range_header("bytes=4-7,0-3,2-6", 10), [(0, 8)])
        self.assertEqual(FileResponse._parse_range_header("bytes=-2", 10), [(8, 10)])
        self.assertEqual(FileResponse._parse_range_header("bytes=" + ",".join(["0-0"] * 101), 10), [])
        with self.assertRaises(MalformedRangeHeader):
            FileResponse._parse_range_header("bytes=" + "0" * 6000 + "a-", 10)

    def test_negative_length_rejected_before_any_stream_read(self):
        class Observed(io.BytesIO):
            def read(self, size=-1):
                raise AssertionError("negative length read body")
        with self.assertRaises(ValueError):
            multipart.parse_form({"Content-Type": b"application/x-www-form-urlencoded",
                                  "Content-Length": b"-1"}, Observed(b"synthetic"), None, None)
        fields, reads = [], []
        class Bounded(io.BytesIO):
            def read(self, size=-1):
                reads.append(size)
                return super().read(size)
        multipart.parse_form({"Content-Type": b"application/x-www-form-urlencoded",
                              "Content-Length": b"3"}, Bounded(b"x=1"), fields.append, None, chunk_size=2)
        self.assertEqual([(f.field_name, f.value) for f in fields], [(b"x", b"1")])
        self.assertTrue(all(0 <= n <= 2 for n in reads))

    def test_configured_filename_cannot_write_outside_upload_directory(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            upload = root / "uploads"
            upload.mkdir()
            outside = root / "sentinel.txt"
            outside.write_bytes(b"unchanged")
            for filename in (os.fsencode(outside), b"../sentinel.txt"):
                item = multipart.File(filename, config={"UPLOAD_DIR": os.fsencode(upload),
                    "UPLOAD_KEEP_FILENAME": True, "UPLOAD_KEEP_EXTENSIONS": True,
                    "MAX_MEMORY_FILE_SIZE": 1})
                try:
                    item.write(b"owned fixture")
                    item.finalize()
                    self.assertEqual(outside.read_bytes(), b"unchanged")
                    self.assertEqual((upload / "sentinel.txt").read_bytes(), b"owned fixture")
                finally:
                    item.close()

    def test_multipart_header_count_and_size_limits(self):
        for headers in (b"X-Test: a\r\n" * 9, b"X-Test: " + b"a" * 5000 + b"\r\n"):
            with self.subTest(size=len(headers)), self.assertRaises(MultipartParseError):
                parser = multipart.MultipartParser(b"fixture")
                parser.write(b"--fixture\r\n" + headers + b"\r\ndata\r\n--fixture--\r\n")
        received = []
        parser = multipart.MultipartParser(b"fixture", {"on_part_data": lambda data, start, end: received.append(data[start:end])})
        parser.write(b"--fixture\r\nX-Test: ordinary\r\n\r\ndata\r\n--fixture--\r\n")
        parser.finalize()
        self.assertEqual(b"".join(received), b"data")

    def test_large_preamble_and_epilogue_keep_legitimate_payload(self):
        received = []
        parser = multipart.MultipartParser(b"fixture", {"on_part_data": lambda data, start, end: received.append(data[start:end])})
        parser.write(b"\r\n" * 32768 + b"--fixture\r\nX: a\r\n\r\ncontrol\r\n--fixture--\r\n" + b"x" * 65536)
        parser.finalize()
        self.assertEqual(b"".join(received), b"control")


class AsyncFrameworkBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_urlencoded_limits_apply_across_stream_chunks(self):
        with self.assertRaises(HTTPException) as count:
            await form(b"a=1&b=2&c=3", max_fields=2)
        self.assertEqual(count.exception.status_code, 400)
        with self.assertRaises(HTTPException) as size:
            await form(b"a=" + b"x" * 32, max_part_size=16)
        self.assertEqual(size.exception.status_code, 400)
        parsed = await form(b"a=1&b=two+words", max_fields=2, max_part_size=16)
        self.assertEqual(dict(parsed), {"a": "1", "b": "two words"})

    async def test_semicolon_never_smuggles_an_overriding_field(self):
        for chunk_size in (1, 7, 100):
            parsed = await form(b"role=user&x=;role=admin", chunk_size=chunk_size)
            self.assertEqual(dict(parsed), {"role": "user", "x": ";role=admin"})
        with self.assertRaises(HTTPException):
            await form(b"a=1&" * 10000, chunk_size=65536, max_fields=8)

    async def test_file_rollover_write_runs_outside_event_loop(self):
        threads = []
        class Observed(SpooledTemporaryFile):
            def write(self, data):
                threads.append(threading.get_ident())
                return super().write(data)
        item = UploadFile(Observed(max_size=8, mode="w+b"))
        try:
            await item.write(b"1234")
            await item.write(b"567890")
            self.assertEqual(threads[0], threading.get_ident())
            self.assertNotEqual(threads[1], threading.get_ident())
            await item.seek(0)
            self.assertEqual(await item.read(), b"1234567890")
        finally:
            await item.close()


if __name__ == "__main__":
    unittest.main()
