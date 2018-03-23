#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import PIL
import PIL.Image
import PyPDF2
from zipfile import ZipFile
import rarfile
import json
import urllib.parse

def getNameAndExtention(path):
    return os.path.splitext(path)

# ファイルリストをpdfに変換
def changeImg2Pdf(filelist, pdflist):
  for srcFile in filelist:
    name, ext = getNameAndExtention(srcFile)
    dstFile = name + '.pdf'

    # イメージをpdfとして保存
    PIL.Image.open(srcFile).save(dstFile, "PDF", resolution = 100.0)
    pdflist.append(dstFile)
  
  return pdflist


def margePdf(pdflist, pdfWriter):
  for file in pdflist:
    pdfReader = PyPDF2.PdfFileReader(file, "rb")
    for pageNum in range(pdfReader.getNumPages()):
      pdfWriter.addPage(pdfReader.getPage(pageNum))


def writePdf(pdfWriter, dstPath):
  with open(dstPath, "wb") as outputs:
    pdfWriter.write(outputs)

# imageをPDFに置き換え
pdflist = []
changeImg2Pdf([
  '../test/0001.jpg',
  '../test/0002.jpg',
  '../test/0003.jpg',
], pdflist)

# PDFの読み書き
pdfWriter = PyPDF2.PdfFileWriter()
margePdf(pdflist, pdfWriter)

dstPath = '../test/marge.pdf'
writePdf(pdfWriter, dstPath)