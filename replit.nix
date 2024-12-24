{pkgs}: {
  deps = [
    pkgs.tesseract     # OCR (Optical Character Recognition) engine
    pkgs.zlib          # Data compression library
    pkgs.tk            # GUI toolkit
    pkgs.tcl           # Programming language
    pkgs.openjpeg      # JPEG 2000 codec
    pkgs.libxcrypt     # Extended crypt library
    pkgs.libwebp       # WebP image format library
    pkgs.libtiff       # TIFF image format library
    pkgs.libjpeg       # JPEG image format library
    pkgs.libimagequant # Image color quantization library
    pkgs.lcms2         # Little CMS color management library
    pkgs.freetype      # Font rendering library
    pkgs.postgresql    # PostgreSQL database
  ];
}
