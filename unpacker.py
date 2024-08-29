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
            caveat_msg = None
            if request.add_extracted(uresult.localpath, uresult.displayname, f'Unpacked from {request.sha256}',
                                     safelist_interface=self.api_interface):
                caveat_msg = "Although the file extracted hasn't been re-submitted due to being known to be safe."
            request.result.add_section(ResultSection(f"{os.path.basename(uresult.displayname)} successfully unpacked!",
                                                     body=caveat_msg))

    def _check_upx(self, packedfile):
        # Test the file to see if UPX agrees with our identification
        stdout, stderr = Popen((self.upx_exe, '-t', packedfile),
                               stdout=PIPE, stderr=PIPE).communicate()
        return (stdout, stderr)

    def _fix_p_info(self, packedfile)
        stream = open(packedfile, 'r+b')
        buff = stream.read()
        upx_index = buff.find(b'UPX!')
        if upx_index == -1:
            self.log.info('Could not find UPX l_info struct')
            return None
        l_info_offset = upx_index - 4
        if l_info_offset < 0:
            self.log.info('Invalid l_info_offset')
            return None
        p_filesize = buff[l_info_offset + 16 : l_info_offset + 20]
        p_blocksize = buff[l_info_offset + 20 : l_info_offset + 24]
        stream.seek(-12, os.SEEK_END)
        filesize = stream.read(4)
        # check p_filesize and p_blocksize of packed file, if corrupt (set to 0), fix it by set the real filesize value
        if p_blocksize  == b'\x00\x00\x00\x00' or p_filesize == b'\x00\x00\x00\x00':
            self.log.info('UPX altered p_blocksize / p_filesize - try to restore')
            stream.seek(l_info_offset + 16)
            stream.write(filesize)
            stream.seek(l_info_offset + 20)
            stream.write(filesize)
            stream.close()

    def _unpack_upx(self, packedfile, outputpath, displayname):
        i = 0
        # run check in while to recheck after fix
        # call fix function if UPX return p_info corrupted
        # used a counter to avoid infinite loop
        while i < 2:
            check_stdout, check_stderr = self._check_upx(packedfile)
            if b'[OK]' in check_stdout and b'Tested 1 file' in check_stdout:
                check = True
                break
            elif b'p_info corrupted' in check_stderr:
                check = False
                self.log.info('UPX File p_info corrupted')
                self._fix_p_info(packedfile)
                i = i+1
            else:
                check = False
                break

        # Check is True when UPX -t validates file - we could try to unpack
        if check is True:
            stdout, stderr = Popen((self.upx_exe, '-d', '-o', outputpath, packedfile),
                                   stdout=PIPE, stderr=PIPE).communicate()

            if b'Unpacked 1 file' in stdout:
                # successfully unpacked.
                return UnpackResult(True, outputpath, displayname, {'stdout': stdout[:1024]})
            else:
                # add a return if unpacking didn't work
                self.log.info(f'UPX extractor failed to unpack file:\n{stderr[:1024]}\n{stderr[:1024]}')

        # Check is True when UPX -t validates file - we could try to unpack
        else:
            self.log.info(f'UPX extractor said this file was not UPX packed:\n{check_stderr[:1024]}\n{check_stderr[:1024]}')
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
