#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
import os
import sys
import re
import datetime
import PIL
import PIL.Image
import PyPDF2
from zipfile import ZipFile
import rarfile
import json
import urllib.parse
import boto3

basedir = '/tmp'
imgExt = ['.jpg', '.png', '.gif']

s3 = boto3.client('s3')  # AWS S3
s3_client = boto3.client('s3')

def getNameAndExtention(path):
    return os.path.splitext(path)

def unzip(zipPath, pdfPath, ext):
    """
    ファイルを解凍
    解凍先はグローバル変数の現在時刻
    """
    print('=== unzip start ===')
    # 拡張子がzipの場合
    if ext == '.zip':
        with ZipFile(zipPath,'r') as inputFile:
            inputFile.extractall(pdfPath)

    # 拡張子がrarの場合
    # if ext == '.rar':
    #     rf = rarfile.RarFile(zipPath)
    #     for f in rf.infolist():
    #         #ファイルの内容を復元
    #         out = open(f.filename, 'w')
    #         out.write(rf.read(f))
    #         out.close()

    os.remove(zipPath) # 元ファイルを削除
    print('=== unzip end ===')

def writePdf(name):
    with open(name, 'wb') as file:
        pass

## 再帰的にファイルを検索 ##
def searchImg(imgList, imgPath):
    global imgExt
    for file in find_all_files(imgPath):
        # 拡張子の取得
        name, ext = getNameAndExtention(file)
        
        if ext.lower() in imgExt:
            imgList.append(file)
    
    return imgList

## searchImgから呼び出される ##
def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        yield root
        for file in files:
            yield os.path.join(root, file)

# ファイルリストをpdfに変換
def changeImg2Pdf(filelist, pdflist):
  for srcFile in filelist:
    name, ext = getNameAndExtention(srcFile)
    dstFile = name + '.pdf'

    # イメージをpdfとして保存
    print(srcFile, dstFile)
    img = PIL.Image.open(srcFile)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(dstFile, "PDF", resolution = 100.0)
    pdflist.append(dstFile)
    os.remove(srcFile) # 元ファイルを削除
  
  # イメージの順をソート
  pdflist.sort()
  return pdflist


def margePdf(pdflist, pdfWriter):
  for file in pdflist:
    pdfReader = PyPDF2.PdfFileReader(file, "rb")
    for pageNum in range(pdfReader.getNumPages()):
      pdfWriter.addPage(pdfReader.getPage(pageNum))


def writePdf(pdfWriter, dstPath):
  with open(dstPath, "wb") as outputs:
    pdfWriter.write(outputs)

## MAIN ##
def lambda_handler(event, context):
    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    print(bucket, key)

    try:
        # バケツの取得
        response = s3.get_object(Bucket=bucket, Key=key)

        # レスポンスの内容の確認
        if response['ContentType'] != 'application/zip' and response['ContentType'] != 'application/x-zip-compressed' and response['ContentType'] != 'binary/octet-stream' :
            return 'Unsupported extension. : ' + response['ContentType']

        # src/yyyymmddhhmmssfff/filename.zip
        keyItems = key.split('/')
        createDate = keyItems[1]
        zipname = keyItems[2]

        # 拡張をpdfに変更
        name, ext = getNameAndExtention(zipname)

        # ワークフォルダと格納パスの作成
        global basedir

        pdfname = name + '.pdf' # pdfのファイル名
        zipPath = os.path.join(basedir, createDate + "_" + zipname) # zipの保存名
        imgPath = os.path.join(basedir, 'img', createDate, name)   # imgの解凍先
        pdfPath = os.path.join(basedir, createDate + "_" + pdfname) # pdfの保存名
        pdfkey = '/'.join(['dst', createDate, pdfname]) # pdfの保存key
        os.makedirs(imgPath, exist_ok=True)
        print(zipPath)
        print(imgPath)
        print(pdfPath)

        # S3から/tmpにダウンロード
        s3_client.download_file(bucket, key, zipPath)

        # 解凍処理
        unzip(zipPath, imgPath, ext)

        # 画像を検索
        imgList = []
        searchImg(imgList, imgPath)

        # imageをPDFに置き換え
        pdflist = []
        changeImg2Pdf(imgList, pdflist)

        # PDFの読み書き
        pdfWriter = PyPDF2.PdfFileWriter()
        margePdf(pdflist, pdfWriter)
        writePdf(pdfWriter, pdfPath)

        # S3にPDFをアップロード 
        s3_client.upload_file(pdfPath, bucket, pdfkey)

        return 'success!!!'

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

