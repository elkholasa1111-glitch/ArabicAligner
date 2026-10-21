# Native build patches

FFmpeg 8.1.3 makedef retains its original Derek Buitenhuis copyright and permissive license. The Windows-only patch reads an object response file and passes a response file to lib.exe, avoiding Windows argument-length truncation. It does not change codec code or enable GPL libraries. The builder also records the make depfile overrides and adjusts the generated SLIB_CREATE_DEF_CMD to write the exact OBJS list with GNU make file(). Unmodified source tarballs plus this patch and the exact builder form the supplied corresponding source. Mac builds do not apply this patch.
