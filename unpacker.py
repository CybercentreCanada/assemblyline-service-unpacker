import os
from collections import namedtuple
from subprocess import PIPE, Popen

from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.result import Result, ResultSection

PACKER_UNKNOWN = 'unknown'
PACKER_UPX = 'upx'

UnpackResult = namedtuple('UnpackResult', ['ok', 'localpath', 'displayname', 'meta'])


class Unpacker(ServiceBase):

    def __init__(self, config=None):
        super(Unpacker, self).__init__(config)
        self.upx_exe = "/usr/bin/upx"
        if not os.path.exists(self.upx_exe):
            raise Exception(f'UPX executable not found on system: {self.upx_exe}')

    def execute(self, request):
        request.result = Result()
        uresult = self._unpack(request, ['upx'])
        if uresult.ok and uresult.localpath:
            request.add_extracted(uresult.localpath, uresult.displayname, f'Unpacked from {request.sha256}')
            request.result.add_section(ResultSection(f"{os.path.basename(uresult.displayname)} successfully unpacked!"))

    def _unpack_upx(self, packedfile, outputpath, displayname):
        # Test the file to see if UPX agrees with our identification.
        stdout, stderr = Popen((self.upx_exe, '-t', packedfile),
            stdout=PIPE, stderr=PIPE).communicate()

        if b'[OK]' in stdout and b'Tested 1 file' in stdout:
             stdout, stderr = Popen((self.upx_exe, '-d', '-o', outputpath, packedfile),
                stdout=PIPE, stderr=PIPE).communicate()

             if b'Unpacked 1 file' in stdout:
                # successfully unpacked.
                return UnpackResult(True, outputpath, displayname, {'stdout': stdout[:1024]})
        else:
            self.log.info(f'UPX extractor said this file was not UPX packed:\n{stderr[:1024]}\n{stderr[:1024]}')
        # UPX unpacking is failure prone due to the number of samples that are identified as UPX
        # but are really some minor variant. For that reason we can't really fail the result
        # every time upx has problems with a file.
        return UnpackResult(True, None, None, None)

    def _unpack(self, request, packer_names):
        for name in packer_names:
            if 'upx' in name.lower():
                packedfile = request.file_path
                unpackedfile = packedfile + '.unUPX'
                displayname = os.path.basename(request.file_path) + '.unUPX'
                return self._unpack_upx(packedfile, unpackedfile, displayname)

        return UnpackResult(True, None, None, None)
