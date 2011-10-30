#!/usr/bin/env python
###############################################################################
# Name: _winrecycle.py                                                        #
# Purpose: Windows recycle bin implementation.                                #
# Author: Kevin D. Smith <Kevin.Smith@sixquickrun.com>                        #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

""" This is a self generating file.  Run it to refresh the recycle.exe data. """

__author__ = "Kevin D. Smith <Kevin.Smith@sixquickrun.com>"
__revision__ = "$Revision: 50825 $"
__scid__ = "$Id: Recycle.py 50825 2007-12-19 07:57:23Z CJP $"

import base64, re

recycle = base64.b64decode(
"TVqQAAMAAAAEAAAA//8AALgAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAgAAAAA4fug4AtAnNIbgBTM0hVGhpcyBwcm9ncmFtIGNhbm5vdCBiZSBydW4gaW4gRE9TIG1vZG"
"UuDQ0KJAAAAAAAAABQRQAATAEFAJHDw0YAGAAADAIAAOAABwMLAQI4AAwAAAAUAAAAAgAAgBIAAAA"
"QAAAAIAAAAABAAAAQAAAAAgAABAAAAAEAAAAEAAAAAAAAAABgAAAABAAAyEMBAAMAAAAAACAAABAA"
"AAAAEAAAEAAAAAAAABAAAAAAAAAAAAAAAABQAAAUAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAC50ZXh0AAAA9AoAAAAQAAAADAAAAAQAAAAAAAA"
"AAAAAAAAAAGAAAGAuZGF0YQAAAEAAAAAAIAAAAAIAAAAQAAAAAAAAAAAAAAAAAABAAADALnJkYXRh"
"AADwAAAAADAAAAACAAAAEgAAAAAAAAAAAAAAAAAAQAAAQC5ic3MAAAAAwAAAAABAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAIAAAMAuaWRhdGEAABQDAAAAUAAAAAQAAAAUAAAAAAAAAAAAAAAAAABAAADAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"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"
"/yXcUEAAkJAAAAAAAAAAAP8l0FBAAJCQAAAAAAAAAAD/JdhQQACQkAAAAAAAAAAA/yXUUEAAkJAAA"
"AAAAAAAAP8lzFBAAJCQAAAAAAAAAAD/JThRQACQkAAAAAAAAAAAVYnlXekH+P//kJCQkJCQkP////"
"/QGkAAAAAAAP////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP////8"
"AAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAA8BpAAAAAAAAAAAAAAAAAAAAAAAD/////AAAAAP//"
"//8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAC1MSUJHQ0NXMzItRUgtMi1TSkxKLUdUSFItTUlOR1czMgAAAHczMl9zaGFyZWRwdHItPnNpe"
"mUgPT0gc2l6ZW9mKFczMl9FSF9TSEFSRUQpACVzOiV1OiBmYWlsZWQgYXNzZXJ0aW9uIGAlcycKAA"
"AuLi8uLi9nY2MvZ2NjL2NvbmZpZy9pMzg2L3czMi1zaGFyZWQtcHRyLmMAAEdldEF0b21OYW1lQSA"
"oYXRvbSwgcywgc2l6ZW9mKHMpKSAhPSAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABUUAAAAAAAAAAAAACgUgAAzFAAA"
"HBQAAAAAAAAAAAAAPhSAADoUAAAwFAAAAAAAAAAAAAACFMAADhRAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAABAUQAATFEAAFxRAABoUQAAeFEAAAAAAAAAAAAAmFEAAKhRAAC4UQAAyFEAANxRAADoUQA"
"A8FEAAPxRAAAIUgAAEFIAABxSAAAoUgAANFIAADxSAABIUgAAVFIAAGBSAABsUgAAAAAAAAAAAAB4"
"UgAAAAAAAAAAAABAUQAATFEAAFxRAABoUQAAeFEAAAAAAAAAAAAAmFEAAKhRAAC4UQAAyFEAANxRA"
"ADoUQAA8FEAAPxRAAAIUgAAEFIAABxSAAAoUgAANFIAADxSAABIUgAAVFIAAGBSAABsUgAAAAAAAA"
"AAAAB4UgAAAAAAAAEAQWRkQXRvbUEAAJwARXhpdFByb2Nlc3MAAACwAEZpbmRBdG9tQQDdAEdldEF"
"0b21OYW1lQQAA4wJTZXRVbmhhbmRsZWRFeGNlcHRpb25GaWx0ZXIAAAAnAF9fZ2V0bWFpbmFyZ3MA"
"PABfX3BfX2Vudmlyb24AAD4AX19wX19mbW9kZQAAAABQAF9fc2V0X2FwcF90eXBlAAAAAHkAX2Nle"
"Gl0AAAAAOkAX2lvYgAAXgFfb25leGl0AAAAhAFfc2V0bW9kZQAAFQJhYm9ydAAcAmF0ZXhpdAAAAA"
"AwAmZmbHVzaAAAAAA5AmZwcmludGYAAAA/AmZyZWUAAHICbWFsbG9jAAAAAHoCbWVtc2V0AAAAAJA"
"Cc2lnbmFsAAAAAJsCc3RyY3B5AAAAAJ8Cc3RybGVuAAAAAEoAU0hGaWxlT3BlcmF0aW9uQQAAAFAA"
"AABQAAAAUAAAAFAAAABQAABLRVJORUwzMi5kbGwAAAAAFFAAABRQAAAUUAAAFFAAABRQAAAUUAAAF"
"FAAABRQAAAUUAAAFFAAABRQAAAUUAAAFFAAABRQAAAUUAAAFFAAABRQAAAUUAAAbXN2Y3J0LmRsbA"
"AAKFAAAFNIRUxMMzIuRExMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAAAPAAAA/v8AAGcBY3J0MS5jAAAAAAAAAAAAAAA"
"AAAAAAAQAAAAAAAAAAQAgAAMBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB4AAABQAQAAAQAgAAMAAAAA"
"ADIAAACAAgAAAQAgAAIAAAAAAEIAAACgAgAAAQAgAAIAX2F0ZXhpdADAAgAAAQAgAAIAX19vbmV4a"
"XTQAgAAAQAgAAIALnRleHQAAAAAAAAAAQAAAAMB3AIAACoAAAAAAAAAAAAAAAAALmRhdGEAAAAAAA"
"AAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAAAAAAAABAAAAAMBCAAAAAAAAAAAAAAAAAA"
"AAAAALmZpbGUAAAAZAAAA/v8AAGcBY3J0c3R1ZmYuYwAAAAAAAAAAAAAAAFUAAADgAgAAAQAgAAIB"
"AAAAAAAAAAAAAAAAAAAAAAAALnRleHQAAADgAgAAAQAAAAMBCQAAAAEAAAAAAAAAAAAAAAAALmRhd"
"GEAAAAAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAAAQAAAABAAAAAMBAAAAAAAAAA"
"AAAAAAAAAAAAAALmZpbGUAAAAkAAAA/v8AAGcBcmVjeWNsZS5jAAAAAAAAAAAAX21haW4AAADwAgA"
"AAQAgAAIALnRleHQAAADwAgAAAQAAAAMBLwEAAAkAAAAAAAAAAAAAAAAALmRhdGEAAAAAAAAAAgAA"
"AAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAAAQAAAABAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAAL"
"nJkYXRhAAAAAAAAAwAAAAMBAwAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAAAsAAAA/v8AAGcBQ1JUZ2"
"xvYi5jAAAAAAAAAAAALnRleHQAAAAgBAAAAQAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAAA"
"AAAAAAgAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAAAQAAAABAAAAAMBAAAAAAAAAAAAAAAA"
"AAAAAAAALmZpbGUAAAA0AAAA/v8AAGcBQ1JUZm1vZGUuYwAAAAAAAAAALnRleHQAAAAgBAAAAQAAA"
"AMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAAAQAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALm"
"JzcwAAAAAQAAAABAAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAAA8AAAA/v8AAGcBdHh0bW9"
"kZS5jAAAAAAAAAAAALnRleHQAAAAgBAAAAQAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAAAQ"
"AAAAAgAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAAAgAAAABAAAAAMBAAAAAAAAAAAAAAAAA"
"AAAAAAALmZpbGUAAABKAAAA/v8AAGcBZ2NjbWFpbi5jAAAAAAAAAAAAAAAAAGUAAAAgAAAABAAAAA"
"MAcC4wAAAAAAAgAAAAAgAAAAMAAAAAAHIAAAAgBAAAAQAgAAIBAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAIUAAABQBAAAAQAgAAIAX19fbWFpbgCwBAAAAQAgAAIALnRleHQAAAAgBAAAAQAAAAMBrQAAAAsA"
"AAAAAAAAAAAAAAAALmRhdGEAAAAgAAAAAgAAAAMBBAAAAAEAAAAAAAAAAAAAAAAALmJzcwAAAAAgA"
"AAABAAAAAMBEAAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAABUAAAA/v8AAGcBcHNldWRvLXJlbG9jLm"
"MAAAAAAAAAAJgAAADQBAAAAQAgAAIBAAAAAAAAAAAAAAAAAAAAAAAALnRleHQAAADQBAAAAQAAAAM"
"BKAAAAAMAAAAAAAAAAAAAAAAALmRhdGEAAAAwAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJz"
"cwAAAAAwAAAABAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAABeAAAA/v8AAGcBY3B1X2ZlY"
"XR1cmVzLmMAAAAAAAAAALMAAAAABQAAAQAgAAIBAAAAAAAAAAAAAAAAAAAAAAAALnRleHQAAAAABQ"
"AAAQAAAAMB+AAAAAsAAAAAAAAAAAAAAAAALmRhdGEAAAAwAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAA"
"AAAAALmJzcwAAAAAwAAAABAAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmZpbGUAAABpAAAA/v8AAGcB"
"Q1JUX2ZwMTAuYwAAAAAAAAAAX2ZwcmVzZXQABgAAAQAgAAIBAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"MgAAAAABgAAAQAgAAIALnRleHQAAAAABgAAAQAAAAMBBwAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAA"
"AwAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABAAAAABAAAAAMBAAAAAAAAAAAAAAA"
"AAAAAAAAALmZpbGUAAAAWAQAA/v8AAGcBAAAAANIAAAAAAAAAAAAAAAAALnRleHQAAAAQBgAAAQAA"
"AAMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAAAwAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAAL"
"mJzcwAAAABAAAAABAAAAAMBAgAAAAAAAAAAAAAAAAAAAAAAAAAAAOYAAAAQAAAAAwAAAAMAAAAAAP"
"cAAAAQBgAAAQAgAAMBAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsBAAAgBgAAAQAgAAMAAAAAADABAAB"
"QAAAABAAAAAMAAAAAAEMBAAAwAAAAAgAAAAMAAAAAAE4BAABgAAAABAAAAAMAAAAAAFsBAAA4AAAA"
"AgAAAAMAAAAAAGYBAADABgAAAQAgAAIALnRleHQAAAAQBgAAAQAAAAMB5QIAACwAAAAAAAAAAAAAA"
"AAALmRhdGEAAAAwAAAAAgAAAAMBEAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABQAAAABAAAAAMBIA"
"AAAAAAAAAAAAAAAAAAAAAALnJkYXRhAAAQAAAAAwAAAAMBwwAAAAAAAAAAAAAAAAAAAAAAcHJvYmU"
"AAAAGCQAAAQAAAAYAZG9uZQAAAAAdCQAAAQAAAAYALnRleHQAAAAACQAAAQAAAAMBLQAAAAAAAAAA"
"AAAAAAAAAAAALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABwAAAAB"
"AAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALnRleHQAAAAwCQAAAQAAAAMBAAAAAAAAAAAAAAAAAAAAAA"
"AALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABwAAAABAAAAAMBAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAIIBAAAwCQAAAQAgAAIBAAAAAAAAAAAAAAAAAAAAAAAALnRleHQA"
"AAAwCQAAAQAAAAMBRwAAAAUAAAAAAAAAAAAAAAAALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAAA"
"AAAAAAAAAAALmJzcwAAAABwAAAABAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALnRleHQAAACACQAAAQ"
"AAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfEAgAABQAAAAM"
"ALmlkYXRhJDX8AAAABQAAAAMALmlkYXRhJDSEAAAABQAAAAMALmlkYXRhJDboAQAABQAAAAMALnRl"
"eHQAAACACQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJ"
"De8AgAABQAAAAMALmlkYXRhJDX0AAAABQAAAAMALmlkYXRhJDR8AAAABQAAAAMALmlkYXRhJDbIAQ"
"AABQAAAAMALnRleHQAAACQCQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAA"
"AAAMALmlkYXRhJDfUAgAABQAAAAMALmlkYXRhJDUMAQAABQAAAAMALmlkYXRhJDSUAAAABQAAAAMA"
"LmlkYXRhJDYQAgAABQAAAAMALnRleHQAAACQCQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzc"
"wAAAABwAAAABAAAAAMALmlkYXRhJDfIAgAABQAAAAMALmlkYXRhJDUAAQAABQAAAAMALmlkYXRhJD"
"SIAAAABQAAAAMALmlkYXRhJDbwAQAABQAAAAMALnRleHQAAACQCQAAAQAAAAMALmRhdGEAAABAAAA"
"AAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfAAgAABQAAAAMALmlkYXRhJDX4AAAABQAA"
"AAMALmlkYXRhJDSAAAAABQAAAAMALmlkYXRhJDbcAQAABQAAAAMALnRleHQAAACgCQAAAQAAAAMAL"
"mRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDe0AgAABQAAAAMALmlkYX"
"RhJDXsAAAABQAAAAMALmlkYXRhJDR0AAAABQAAAAMALmlkYXRhJDaoAQAABQAAAAMALnRleHQAAAC"
"wCQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfsAgAA"
"BQAAAAMALmlkYXRhJDUkAQAABQAAAAMALmlkYXRhJDSsAAAABQAAAAMALmlkYXRhJDZUAgAABQAAA"
"AMALnRleHQAAADACQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALm"
"lkYXRhJDe4AgAABQAAAAMALmlkYXRhJDXwAAAABQAAAAMALmlkYXRhJDR4AAAABQAAAAMALmlkYXR"
"hJDa4AQAABQAAAAMALnRleHQAAADQCQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABw"
"AAAABAAAAAMALmlkYXRhJDfMAgAABQAAAAMALmlkYXRhJDUEAQAABQAAAAMALmlkYXRhJDSMAAAAB"
"QAAAAMALmlkYXRhJDb8AQAABQAAAAMALnRleHQAAADgCQAAAQAAAAMALmRhdGEAAABAAAAAAgAAAA"
"MALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDewAgAABQAAAAMALmlkYXRhJDXoAAAABQAAAAMALml"
"kYXRhJDRwAAAABQAAAAMALmlkYXRhJDaYAQAABQAAAAMALnRleHQAAADwCQAAAQAAAAMALmRhdGEA"
"AABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfoAgAABQAAAAMALmlkYXRhJDUgA"
"QAABQAAAAMALmlkYXRhJDSoAAAABQAAAAMALmlkYXRhJDZIAgAABQAAAAMALnRleHQAAAAACgAAAQ"
"AAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfwAgAABQAAAAM"
"ALmlkYXRhJDUoAQAABQAAAAMALmlkYXRhJDSwAAAABQAAAAMALmlkYXRhJDZgAgAABQAAAAMALnRl"
"eHQAAAAQCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJ"
"Df0AgAABQAAAAMALmlkYXRhJDUsAQAABQAAAAMALmlkYXRhJDS0AAAABQAAAAMALmlkYXRhJDZsAg"
"AABQAAAAMALnRleHQAAAAgCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAA"
"AAAMALmlkYXRhJDfgAgAABQAAAAMALmlkYXRhJDUYAQAABQAAAAMALmlkYXRhJDSgAAAABQAAAAMA"
"LmlkYXRhJDY0AgAABQAAAAMALnRleHQAAAAwCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzc"
"wAAAABwAAAABAAAAAMALmlkYXRhJDfkAgAABQAAAAMALmlkYXRhJDUcAQAABQAAAAMALmlkYXRhJD"
"SkAAAABQAAAAMALmlkYXRhJDY8AgAABQAAAAMALnRleHQAAABACgAAAQAAAAMALmRhdGEAAABAAAA"
"AAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfQAgAABQAAAAMALmlkYXRhJDUIAQAABQAA"
"AAMALmlkYXRhJDSQAAAABQAAAAMALmlkYXRhJDYIAgAABQAAAAMALnRleHQAAABQCgAAAQAAAAMAL"
"mRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfYAgAABQAAAAMALmlkYX"
"RhJDUQAQAABQAAAAMALmlkYXRhJDSYAAAABQAAAAMALmlkYXRhJDYcAgAABQAAAAMALnRleHQAAAB"
"gCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDfcAgAA"
"BQAAAAMALmlkYXRhJDUUAQAABQAAAAMALmlkYXRhJDScAAAABQAAAAMALmlkYXRhJDYoAgAABQAAA"
"AMALmZpbGUAAAAmAQAA/v8AAGcBZmFrZQAAAAAAAAAAAAAAAAAAaG5hbWUAAABwAAAABQAAAAMAZn"
"RodW5rAADoAAAABQAAAAMALnRleHQAAABwCgAAAQAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGE"
"AAABAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABwAAAABAAAAAMBAAAAAAAAAAAA"
"AAAAAAAAAAAALmlkYXRhJDIUAAAABQAAAAMBFAAAAAMAAAAAAAAAAAAAAAAALmlkYXRhJDXkAAAAB"
"QAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDRsAAAABQAAAAMBBAAAAAAAAAAAAAAAAAAAAA"
"AALmZpbGUAAABXAQAA/v8AAGcBZmFrZQAAAAAAAAAAAAAAAAAALnRleHQAAABwCgAAAQAAAAMBAAA"
"AAAAAAAAAAAAAAAAAAAAALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAA"
"AABwAAAABAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDS4AAAABQAAAAMBBAAAAAAAAAAAA"
"AAAAAAAAAAALmlkYXRhJDUwAQAABQAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDf4AgAABQ"
"AAAAMBCwAAAAAAAAAAAAAAAAAAAAAALnRleHQAAABwCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAM"
"ALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDecAgAABQAAAAMALmlkYXRhJDXcAAAABQAAAAMALmlk"
"YXRhJDRkAAAABQAAAAMALmlkYXRhJDZ4AQAABQAAAAMALnRleHQAAACACgAAAQAAAAMALmRhdGEAA"
"ABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDeQAgAABQAAAAMALmlkYXRhJDXQAA"
"AABQAAAAMALmlkYXRhJDRYAAAABQAAAAMALmlkYXRhJDZMAQAABQAAAAMALnRleHQAAACQCgAAAQA"
"AAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDeYAgAABQAAAAMA"
"LmlkYXRhJDXYAAAABQAAAAMALmlkYXRhJDRgAAAABQAAAAMALmlkYXRhJDZoAQAABQAAAAMALnRle"
"HQAAACgCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJD"
"eUAgAABQAAAAMALmlkYXRhJDXUAAAABQAAAAMALmlkYXRhJDRcAAAABQAAAAMALmlkYXRhJDZcAQA"
"ABQAAAAMALnRleHQAAACwCgAAAQAAAAMALmRhdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAA"
"AAMALmlkYXRhJDeMAgAABQAAAAMALmlkYXRhJDXMAAAABQAAAAMALmlkYXRhJDRUAAAABQAAAAMAL"
"mlkYXRhJDZAAQAABQAAAAMALmZpbGUAAABnAQAA/v8AAGcBZmFrZQAAAAAAAAAAAAAAAAAAaG5hbW"
"UAAABUAAAABQAAAAMAZnRodW5rAADMAAAABQAAAAMALnRleHQAAADACgAAAQAAAAMBAAAAAAAAAAA"
"AAAAAAAAAAAAALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmJzcwAAAABwAAAA"
"BAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDIAAAAABQAAAAMBFAAAAAMAAAAAAAAAAAAAA"
"AAALmlkYXRhJDXIAAAABQAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDRQAAAABQAAAAMBBA"
"AAAAAAAAAAAAAAAAAAAAAALmZpbGUAAAB8AQAA/v8AAGcBZmFrZQAAAAAAAAAAAAAAAAAALnRleHQ"
"AAADACgAAAQAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmRhdGEAAABAAAAAAgAAAAMBAAAAAAAAAAAA"
"AAAAAAAAAAAALmJzcwAAAABwAAAABAAAAAMBAAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDRoAAAAB"
"QAAAAMBBAAAAAAAAAAAAAAAAAAAAAAALmlkYXRhJDXgAAAABQAAAAMBBAAAAAAAAAAAAAAAAAAAAA"
"AALmlkYXRhJDegAgAABQAAAAMBDQAAAAAAAAAAAAAAAAAAAAAALnRleHQAAADACgAAAQAAAAMALmR"
"hdGEAAABAAAAAAgAAAAMALmJzcwAAAABwAAAABAAAAAMALmlkYXRhJDcEAwAABQAAAAMALmlkYXRh"
"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"
"AF9fX2RvX2dsb2JhbF9jdG9ycwBfX3BlaTM4Nl9ydW50aW1lX3JlbG9jYXRvcgBfX19jcHVfZmVhd"
"HVyZXNfaW5pdABfX2ZwcmVzZXQAcHNldWRvLXJlbG9jLWxpc3QuYwBfdzMyX2F0b21fc3VmZml4AF"
"9fX3czMl9zaGFyZWRwdHJfZGVmYXVsdF91bmV4cGVjdGVkAF9fX3czMl9zaGFyZWRwdHJfZ2V0AGR"
"3Ml9vYmplY3RfbXV0ZXguMABkdzJfb25jZS4xAHNqbF9mY19rZXkuMgBzamxfb25jZS4zAF9fX3cz"
"Ml9zaGFyZWRwdHJfaW5pdGlhbGl6ZQBfX19lcHJpbnRmAF9fX3NqbGpfaW5pdF9jdG9yAF9fX1JVT"
"lRJTUVfUFNFVURPX1JFTE9DX0xJU1RfXwBfX2ltcF9fX3NldG1vZGUAX19kYXRhX3N0YXJ0X18AX1"
"9fRFRPUl9MSVNUX18AX19pbXBfX19vbmV4aXQAX19fcF9fZm1vZGUAX1NldFVuaGFuZGxlZEV4Y2V"
"wdGlvbkZpbHRlckA0AF9fX3czMl9zaGFyZWRwdHJfdGVybWluYXRlAF9fX3Rsc19zdGFydF9fAF9f"
"bGlibXN2Y3J0X2FfaW5hbWUAX19pbXBfX0ZpbmRBdG9tQUA0AF9faW1wX19hYm9ydABfX3NpemVfb"
"2Zfc3RhY2tfY29tbWl0X18AX19zaXplX29mX3N0YWNrX3Jlc2VydmVfXwBfX21ham9yX3N1YnN5c3"
"RlbV92ZXJzaW9uX18AX19fY3J0X3hsX3N0YXJ0X18AX0FkZEF0b21BQDQAX19fY3J0X3hpX3N0YXJ"
"0X18AX19fY2hrc3RrAF9fX2NydF94aV9lbmRfXwBfX2ltcF9fX19wX19lbnZpcm9uAF9faW1wX19f"
"aW9iAF9fYnNzX3N0YXJ0X18AX19fUlVOVElNRV9QU0VVRE9fUkVMT0NfTElTVF9FTkRfXwBfX3Npe"
"mVfb2ZfaGVhcF9jb21taXRfXwBfX2ltcF9fU0hGaWxlT3BlcmF0aW9uQUA0AF9fX3BfX2Vudmlyb2"
"4AX19fY3J0X3hwX3N0YXJ0X18AX19fY3J0X3hwX2VuZF9fAF9faW1wX19zaWduYWwAX19taW5vcl9"
"vc192ZXJzaW9uX18AX19pbXBfX2F0ZXhpdABfX2hlYWRfbGlibXN2Y3J0X2EAX19pbWFnZV9iYXNl"
"X18AX19oZWFkX2xpYnNoZWxsMzJfYQBfX3NlY3Rpb25fYWxpZ25tZW50X18AX19SVU5USU1FX1BTR"
"VVET19SRUxPQ19MSVNUX18AX19pbXBfX19fcF9fZm1vZGUAX0V4aXRQcm9jZXNzQDQAX19kYXRhX2"
"VuZF9fAF9fX2dldG1haW5hcmdzAF9fX3czMl9zaGFyZWRwdHIAX19DVE9SX0xJU1RfXwBfX19zZXR"
"fYXBwX3R5cGUAX19ic3NfZW5kX18AX19DUlRfZm1vZGUAX19fY3J0X3hjX2VuZF9fAF9fX2NydF94"
"Y19zdGFydF9fAF9fX0NUT1JfTElTVF9fAF9faW1wX19HZXRBdG9tTmFtZUFAMTIAX19maWxlX2Fsa"
"WdubWVudF9fAF9faW1wX19tYWxsb2MAX19tYWpvcl9vc192ZXJzaW9uX18AX19EVE9SX0xJU1RfXw"
"BfX2ltcF9fZnByaW50ZgBfX2ltcF9fbWVtc2V0AF9fc2l6ZV9vZl9oZWFwX3Jlc2VydmVfXwBfX19"
"jcnRfeHRfc3RhcnRfXwBfX3N1YnN5c3RlbV9fAF9faW1wX19zdHJsZW4AX19pbXBfX2ZmbHVzaABf"
"X2ltcF9fc3RyY3B5AF9fX3czMl9zaGFyZWRwdHJfdW5leHBlY3RlZABfX2ltcF9fX19nZXRtYWluY"
"XJncwBfX190bHNfZW5kX18AX19pbXBfX0V4aXRQcm9jZXNzQDQAX19fY3B1X2ZlYXR1cmVzAF9faW"
"1wX19mcmVlAF9faW1wX19TZXRVbmhhbmRsZWRFeGNlcHRpb25GaWx0ZXJANABfX21ham9yX2ltYWd"
"lX3ZlcnNpb25fXwBfX2xvYWRlcl9mbGFnc19fAF9fQ1JUX2dsb2IAX19zZXRtb2RlAF9faW1wX19B"
"ZGRBdG9tQUA0AF9faGVhZF9saWJrZXJuZWwzMl9hAF9faW1wX19fY2V4aXQAX19taW5vcl9zdWJze"
"XN0ZW1fdmVyc2lvbl9fAF9fbWlub3JfaW1hZ2VfdmVyc2lvbl9fAF9faW1wX19fX3NldF9hcHBfdH"
"lwZQBfU0hGaWxlT3BlcmF0aW9uQUA0AF9GaW5kQXRvbUFANABfX2xpYnNoZWxsMzJfYV9pbmFtZQB"
"fR2V0QXRvbU5hbWVBQDEyAF9fUlVOVElNRV9QU0VVRE9fUkVMT0NfTElTVF9FTkRfXwBfX2xpYmtl"
"cm5lbDMyX2FfaW5hbWUAX19fY3J0X3h0X2VuZF9fAA==")

# Embed the recycle program for windows into this module
if __name__ == '__main__':
    s = base64.b64encode(open('recycle.exe').read())
    lines = list()
    for piece in xrange(0, (len(s)/77)):
        lines.append(s[(piece*77):(piece*77)+77])
    lines.append(s[(len(s)/77)*77:])
    line = [ "\"%s\"" % x for x in lines ]
    prog = "\n".join(line)
    module = open('_winrecycle.py').read()
    module = re.compile(r'^recycle = .+$\)', re.M).sub(r"recycle = base64.b64decode(\n%s)" % prog, module)
    open('_winrecycle.py','w').write(module)
    print "Embedding was ok?", ''.join(lines) == s
