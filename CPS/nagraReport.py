import xml.etree.ElementTree as ET
from xml.dom import minidom
from PIL import Image, ImageDraw
import os, sys
import imghdr
import argparse
import glob
import re
from datetime import datetime
import binascii
import zlib
#import cv2 as cv
#import numpy as np
sct_table={'M88CS8001':'00 2936 0202','M88CS8001B':'00 2936 0204', 'M88CS8051B':'00 2936 0205'}




def calculate_crc32(hex_string):
    # Remove any whitespace and '0x' prefixes
    clean_hex = hex_string.replace(" ", "").replace("0x", "")
    
    # Convert hex string to bytes
    try:
        data = binascii.unhexlify(clean_hex)
    except binascii.Error as e:
        return f"Error: Invalid hex string - {e}"
    
    # Calculate CRC32
    crc = zlib.crc32(data) & 0xFFFFFFFF  # Ensure unsigned 32-bit
    
    # Return as hex string
    return f"{crc:08X}"

class XMLObject:
  def __init__ (self, Ent, img):
    bndbox=Ent.find('bndbox')
    self.startx=int(bndbox.find('xmin').text)
    self.starty=int(bndbox.find('ymin').text)
    self.endx=int(bndbox.find('xmax').text)
    self.endy=int(bndbox.find('ymax').text) 
    self.name = Ent.find('name').text
    self.pose = Ent.find('pose').text
    self.img = img
  def crop(self):
    return self.img.crop((self.startx, self.starty, self.endx, self.endy))

class XMLImage:
  def __init__ (self, imgEnt, img, xmlPath="", imgPath="", savePath=""):
    self.imgName=imgEnt.find('filename').text
    self.img = img
    if (xmlPath == ""):
      self.imgNamemgPath=imgEnt.find('path').text
    else:
      self.imgPath=imgPath
      
    self.xmlPath=xmlPath
    self.savePath=savePath

    imgSource=imgEnt.find('source')
    self.dBaseName=imgSource.find('database').text
    
    imgSize=imgEnt.find('size')
    self.width=int(imgSize.find('width').text)
    self.height=int(imgSize.find('height').text)
    self.depth=int(imgSize.find('depth').text)
    
    self.xmlObjList=imgEnt.findall('object')
    self.objList=[]
    for obj in self.xmlObjList:
       self.objList.append(XMLObject(obj, img))
    
    for obj in self.objList:
      print("(",obj.startx, obj.starty, obj.endx, obj.endy, obj.name, ")", obj.endx-obj.startx, obj.endy - obj.starty, round((obj.endy - obj.starty)/(obj.endx-obj.startx),2))


  def saveObjectImage (self, savelist=[]):
     saveName=self.imgName.replace(' ', '_')
     f, e = os.path.splitext(saveName)
     #print(f, e)
     for obj in self.objList:
#      print(f+'_'+obj.name+e, '       ', obj.name)
      cropImg=obj.crop()
      cropImg.save(self.savePath+f+'_'+obj.name+e)
      #cropImg.show()

  def drawBBox (self, color=(0,0,255), lWidth=3):
     newImg = self.img
     draw = ImageDraw.Draw(newImg)
     
     for obj in self.objList:
       draw.rectangle([(obj.startx, obj.starty),(obj.endx,obj.endy)], fill=None, outline="red", width=lWidth)

     return newImg
    

def parse_xml(xmlfile):
    
    body=xmlfile.find('BODY')
    socall=body.findall('SOC')
    xmllstall=[]
    for socidx in socall:
        result = {
            'serial': socidx.attrib['serial'],
            'layer2_key': socidx.find('LAYER2_KEY').text,
            'perso': {},
            'cks': []
        }
        
        for perso in socidx.findall('PERSO'):
            result['perso'][perso.attrib['name']] = {
                'value': perso.text.lower(),
                'enc': perso.attrib.get('enc')  # enc is optional
        }

        # Parse all CK elements
        for ck in socidx.findall('CK'):
            result['cks'].append({
                'name': ck.attrib['name'],
                'algo': ck.attrib['algo'],
                'value': ck.text
        })
        print("result", result)
        xmllstall.append(result)   
    return xmllstall

def parse_file(file_path):
    """
    Reads and parses each line of a file.
    
    Args:
        file_path (str): Path to the file to be parsed.
    """
    production_line=[]
    try:
        
        with open(file_path, 'r') as file:
            for line_number, line in enumerate(file, start=1):
                # Remove leading/trailing whitespace and newline characters
                cleaned_line = line.strip()
                
                # Here you can add your specific parsing logic
                # For demonstration, we'll just print the line with its number
                print(f"Line {line_number}: {cleaned_line}")
                
                # Example parsing: Split line into words
                words = cleaned_line.split()
                
                
                testerline=(words[0]+words[1]).split(";")
                station=testerline[0].split(":")
                partnum=testerline[1].split(":")
                print(f"  Words: {words}")
                casidline=words[2].split(":")
                dateline=words[3]+" "+words[4]
                match = re.match(r"Time:(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})", dateline)
                if match:
                    year, month, day, hour, minute, second = map(int, match.groups())
                print(f"  casid: {casidline[1]}")
                print(f"  date: {year}, {month}, {day}, {hour}, {minute}, {second}")
                # Create fixed-length date formats
                dt = datetime.strptime(dateline.split("Time:")[1], "%Y-%m-%d %H:%M:%S")
                #fixed_length_date1 = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"  # YYYY-MM-DD
                #fixed_length_date2 = f"{dt.month:02d}/{dt.day:02d}/{dt.year:04d}"   # MM/DD/YYYY
                #fixed_length_date3 = f"{dt.day:02d}.{dt.month:02d}.{dt.year:04d}"   # DD.MM.YYYY
                ## Print results
                #print("Original parsed datetime:", dt)
                #print("\nFixed-length date formats:")
                #print("ISO format (YYYY-MM-DD):", fixed_length_date1)
                #print("US format (MM/DD/YYYY):", fixed_length_date2)
                #print("European format (DD.MM.YYYY):", fixed_length_date3)
                production_line.append({station[0]:station[1], partnum[0]:partnum[1], casidline[0]:casidline[1], "Time":dt})
                

                # Add your custom parsing logic here
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except IOError:
        print(f"Error: Could not read file '{file_path}'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return production_line

def generate_report(xmlAll, txtAll, PartNumber):
    report=[]
    # Create root element with namespaces
    parts=PartNumber.split("-")
    cts=sct_table[parts[0]]
    try:
        cts=sct_table[parts[0]]
    except KeyError:
        print("Partnumber not found in sct_table")
        # Handle the error case here
        cts = None  # Default value
    if cts == None:
        exit()
    
    
    
    #root = ET.Element(
    #    "{http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00}SignedLogs",
    #    {
    #        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    #        "xmlns": "http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00",
    #        "xsi:schemaLocation": "http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00 CPR_XXX.xsd"
    #    }
    #)

    # Define namespaces
    DEFAULT_NS = "http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

    # Register namespaces to avoid ns0 prefixes
    ET.register_namespace('', DEFAULT_NS)
    ET.register_namespace('xsi', XSI_NS)

    # Create root element with namespaces and schema location
    root = ET.Element(f"{{{DEFAULT_NS}}}SignedLogs",    
                 attrib={
                     f"{{{XSI_NS}}}schemaLocation": 
                     "http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00 CPR_XXX.xsd"
                 })


    # Create Header element
    header_dict={
        "ChipsetTypeString": cts,
        "ChipsetReferenceCutRelease": parts[2],
        "ChipsetReferenceExtension": parts[1],
        "EAT": "0000000000000021",
        "Port": "2502",
        "IP": "::10.252.8.21",
        "FormatVersion": "02.00.00"
    }
    
    header = ET.SubElement(
        root,
        "{http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00}Header",
        header_dict
    )

    nt = datetime.now()
    nt_format = f"{nt.year:04d}/{nt.month:02d}/{nt.day:02d} {nt.hour:02d}:{nt.minute:02d}"
    
    
    # Create Logs element
    logs_head_dict={
        "CreationDate": "",
        "NumberOfRecords": str(len(txtAll))
    }
    
    logs = ET.SubElement(
        root,
        "{http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00}Logs",
        logs_head_dict
    )
    
    
    for prod_chip in txtAll:
        uuid = prod_chip['casid']
        dt = prod_chip['Time']
        #Hi for bb_chip in xmlAll:
        match_bb={}
        for bb_idx in xmlAll:
            bb_uuid=bb_idx['perso']['CPD-OTP:NUID']['value']
            if len(bb_uuid) != 16:
                print ('UUID length in correct in black box file, value={bb_uuid}')
                exit()
            if uuid == bb_uuid:
                match_bb=bb_idx
                break
        if match_bb == {}:
            print('No matched BB data found, uuid = {uuid}')
            exit()
        bb_cn = match_bb['cks'][0]['value']
        fixed_length_date1 = f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"
        input_hex = "0x"+uuid[8:].upper()+" "+bb_cn+" 00"
        
        
        crc32_result = calculate_crc32(input_hex)
        # Create LogRecord element
        log_dict={
            "NUID": uuid[8:],
            "VUID": "",
            "CN": bb_cn,
            "CCN": "",
            "ACK": "00",
            "CRC-32": crc32_result,
            "DeliveryDate": fixed_length_date1
        }
    
        log_record = ET.SubElement(
            logs,
            "{http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00}LogRecord",
            log_dict
        )
        
        
        
    #log_record = ET.SubElement(
    #    logs,
    #    "{http://xmlns.nagra.com/PLM/EBO/SignedLog/02.00.00}LogRecord",
    #    {
    #        "NUID": "cae4fa64",
    #        "VUID": "b42920b501380219",
    #        "CN": "528bbbcf",
    #        "CCN": "908acd6651660c1d",
    #        "ACK": "00",
    #        "CRC-32": "3e43ff82",
    #        "DeliveryDate": "2025/02/28 00:00"
    #    }
    #)

    # Convert to string with pretty formatting
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
    return pretty_xml, nt

    # Generate and print the XML
    #xml_output = create_signed_logs_xml()
    #print(xml_output)
    
    
    
    
    
    
    
    
    #return report


def retrieve(txtPath, xmlPath, datapath):
    xmldirs = os.listdir( xmlPath )
    txtdirs = os.listdir( txtPath )
    report_partnumber={'2769170130.txt':'M88CS8001B-SGC0-A1', '2825462930.txt':'M88CS8001-TGG0-A2', '2827412630.txt':'M88CS8001-SGG0-A3'}

    if xmlPath[-1] != "/":
        xmlPath=xmlPath+"/"
    if txtPath[-1] != "/":
         txtPath=txtPath+"/"
   
    xmlAll=[]
    partnumber=None

    for item in xmldirs:
        if os.path.isfile(xmlPath+item):
            f, e = os.path.splitext(item)
            if (e=='.xml'):
              xmlfile=ET.parse(xmlPath+item)
              xmlparse=parse_xml(xmlfile)
              xmlAll=xmlAll+xmlparse
    
    txtAll=[]
    idx=0
    for item in txtdirs:
        if os.path.isfile(txtPath+item):
            f, e = os.path.splitext(item)
            if (e=='.txt'):
              try:
                 partnumber=report_partnumber[item]
              except KeyError:
                 print("Partnumber not found in sct_table")
                      # Handle the error case here
                 partnumber = None  # Default value
              
                
              txtfile=parse_file(txtPath+item)
              txtAll=txtAll+txtfile
              if partnumber == None:
                  print("No matched partnumber found item = {item}")
                  exit()
              parts=partnumber.split("-")
              filerptxml, nt=generate_report(xmlAll, txtfile, partnumber)
              nt_format = f"{nt.year:04d}/{nt.month:02d}/{nt.day:02d} {nt.hour:02d}:{nt.minute:02d}"
              nt_file   = f"{nt.year:04d}{nt.month:02d}{nt.day:02d}"
              cts=sct_table[parts[0]]
              cts_number = cts.replace(" ", "")
              print(f"idx={idx:04d}")
              print("parts = {parts}")
              file_name = 'MTG_'+cts_number+"_"+parts[2]+"_"+parts[1]+"_"+nt_file+"_"+f"{idx:04d}"
              with open(file_name+".xml", 'w') as f:
                  f.write(filerptxml)
              idx=idx+1    
    #rptxml=generate_report(xmlAll, txtAll, 'M88CS8001-SGG0')
    #with open(datapath, 'w') as f:
        #f.write(rptxml)

print("XML file has been written to 'signed_logs.xml'")
#              imgname=glob.glob(imgPath+f+".*")
#              for imgItem in imgname:
##                  if(imghdr.what(imgItem)!=None):
#                      img = Image.open(imgItem)
#                      xmlImage=XMLImage(xmlfile, img, xmlPath, imgPath, datapath)
#                      xmlImage.saveObjectImage()
#            

def drawBBox(imgPath, xmlPath, datapath):
    xmldirs = os.listdir( xmlPath )
    imgdirs = os.listdir( imgPath )
    for item in xmldirs:
        if os.path.isfile(xmlPath+item):
            f, e = os.path.splitext(item)
            if (e=='.xml'):
              xmlfile=ET.parse(xmlPath+item)
              imgname=glob.glob(imgPath+f+".*")
              for imgItem in imgname:
#                  if(imghdr.what(imgItem)!=None):
                img = Image.open(imgItem)
                xmlImage=XMLImage(xmlfile, img, xmlPath, imgPath, datapath)
                      
                newImg=xmlImage.drawBBox()
                saveName= xmlImage.imgName.replace(' ', '_')
                f, e = os.path.splitext(saveName)
                newImg.save(xmlImage.savePath+f+'_bbx'+e)
                      



      



path = "./"

parser = argparse.ArgumentParser()
# PATH
parser.add_argument('datapath', nargs='?', type=str, default=path, help='Destination Path')
# size Height
parser.add_argument('-t', '--txtPath', type=str, default=path, help='Txt Path')
# size Width
parser.add_argument('-x', '--xmlPath', type=str, default=path, help='XML Path')

#parser.add_argument('-x', '--xmlPath', type=str, default=path, help='XML Path')

args = parser.parse_args()
print(args)
print(args.txtPath, args.xmlPath, args.datapath)



input_hex = "0x26A5C6B9 38D67CB2 42670001 9FAE70ED 54BAD48B 70EA2A1D 51F781FD 00"

# Calculate and print the CRC32
crc32_result = calculate_crc32(input_hex)
print(f"CRC-32 of '{input_hex}': {crc32_result}")



retrieve(args.txtPath, args.xmlPath, args.datapath)




 



