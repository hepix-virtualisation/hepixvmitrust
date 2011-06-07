#!/usr/bin/env python

import codecs
import optparse
import os
import sys
import hashlib
import os.path
# needed for the signing of images.
import M2Crypto.SMIME 
import M2Crypto.BIO 
import M2Crypto.SMIME
import uuid
# simplejson is included with Python 2.6 and above
# with the name json
if float(sys.version[:3]) >= 2.6:
    import json
else:
    # python 2.4 or 2.5 can also import simplejson
    # as working alternative to the json included.
    import simplejson as json

import datetime
import time
import logging, logging.config

# Set up teh logging library
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

h = NullHandler()
logging.getLogger("hepixvmitrust.vmitrustlib").addHandler(h)
logger = logging.getLogger("hepixvmitrust.vmitrustlib")
time_required_metadata = [u'dc:date:created', 
        u'dc:date:expires',
    ]
time_required_metadata_set = set(time_required_metadata)

endorser_required_metadata = [u'hv:ca',
        u'hv:dn',
        u'hv:email',
        u'dc:creator',
    ]
endorser_required_metadata_set = set(endorser_required_metadata)

image_required_metadata = [u'dc:title',
        u'dc:description',
        u'hv:size',
        u'sl:checksum:sha512',
        u'sl:arch',
        u'hv:uri',
        u'dc:identifier',
        u'sl:os',
        u'sl:osversion',
        u'sl:comments',
        u'hv:hypervisor',
        u'hv:version',
    ]
image_required_metadata_set = set(image_required_metadata)


imagelist_required_metadata = [u'dc:date:created',
        u'dc:date:expires',
        u'dc:identifier',
        u'dc:description',
        u'dc:title',
        u'dc:source',
        u'hv:version',
        u'hv:uri',
    ]
imagelist_required_metadata_set = set(imagelist_required_metadata)

imagelist_required_metadata_types = [u'hv:endorser',
        u'hv:images',
    ]
imagelist_required_metadata_types_set = set(imagelist_required_metadata_types)


time_format_definition = "%Y-%m-%dT%H:%M:%SZ"

class EndorserModel:
    def __init__(self,metadata = {}):
        self.metadata = metadata


class ImageModel:    
    def __init__(self,metadata = {}):
        self.metadata = metadata

class ListModel:
    interestingkeys = set([u'vmi_uid'])
    def __init__(self,metadata = {},images=[],endorser=EndorserModel()):
        self.endorser = endorser
        self.metadata = metadata
        self.images = images

        
class VMimageListEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, EndorserModel):
            return self.vm_endorser_encode(obj)
        if isinstance(obj, ImageModel):
            return self.vm_image_encode(obj)
        if isinstance(obj, ListModel):
            return self.vm_imagelist_encode(obj)
        if isinstance(obj, datetime.datetime):
            return self.datetime_encode(obj)
        return json.JSONEncoder.default(obj)

    def vm_image_encode(self, obj):
        if not obj.metadata.has_key(u'dc:identifier'):
            obj.metadata[u'dc:identifier'] = str(uuid.uuid4())
        for field in image_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        return {u'hv:image' : obj.metadata}

    def vm_imagelist_encode(self, obj):    
        if not obj.metadata.has_key(u'dc:identifier'):
            obj.metadata[u'dc:identifier'] = str(uuid.uuid4())
        if not obj.metadata.has_key(u'dc:date:created'):
            now = datetime.datetime.utcnow()
            obj.metadata[u'dc:date:created'] = now
        if not obj.metadata.has_key(u'dc:date:expires'):
            now = datetime.datetime.utcnow()
            servicelength = datetime.timedelta(weeks=4)
            expiry = now + servicelength
            obj.metadata[u'dc:date:expires'] = expiry
        imagelist = []
        for i in obj.images:
            tmp_data = self.default(i)
            if tmp_data == None:
                return json.JSONEncoder.default(self, obj)
            else:
                imagelist.append(self.default(i))
        for field in imagelist_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        output = {u'hv:images' : imagelist,
            u'hv:endorser' : self.default(obj.endorser)}
        for key in obj.metadata.keys():
            output[key] = obj.metadata[key]
        # Now we encode as the broken format so we can read old fromat and write old format.
        # 
        return output
        # This will be released after the next major release 0.10
        return {u'hv:imagelist' : output}
    
    def vm_endorser_encode(self, obj):
        for field in endorser_required_metadata:
            if not obj.metadata.has_key(field):
                obj.metadata[field] = ''
        return {u'hv:x509' : obj.metadata}
    def datetime_encode(self, obj):
        return obj.strftime(time_format_definition)

def VMendorserDecoder(dct):
    if not u'hv:x509' in dct.keys():
        return None
    metadata = dct[u'hv:x509']
    if metadata == None:
        
        logger.error( "coding error=%s" % (dct))
        return None
    if not endorser_required_metadata_set.issubset(metadata.keys()):    
        logger.error( "coding error2=%s" % (dct))
        return None
    #print "VMendorserDecoder.metadata=%s" % (metadata)
    return EndorserModel(metadata=metadata)

def VMimageDecoder(dct):
    if not u'hv:image' in dct.keys():
        return None
    metadata = dct[u'hv:image']
    if metadata == None:
        logger.error("coding error=%s" % (dct))
        return None
    if not image_required_metadata_set.issubset(metadata.keys()):    
        logger.error("coding error2=%s" % (dct))
        return None
    return ImageModel(metadata=metadata)




def VMimageListDecoder(dictionary):
    if not isinstance(dictionary, dict):
        return None
    dict_keys = set(dictionary.keys())
    if not imagelist_required_metadata_set.issubset(dict_keys):
        return None
    if not time_required_metadata_set.issubset(dict_keys):
        return None
    if not dictionary.has_key(u'hv:endorser'):
        return None
    if not dictionary.has_key(u'hv:images'):
        return None
    endorser_dct = dictionary[u'hv:endorser']
    imagelist = dictionary[u'hv:images']
    allimages = []
    for image in imagelist:
        translatedimage = VMimageDecoder(image)
        if not translatedimage == None:
            allimages.append(translatedimage)
    imagelistmetadata = {}
    endorser = VMendorserDecoder(endorser_dct)
    if endorser == None:
        return None
    copyfield = dict_keys.difference(time_required_metadata + imagelist_required_metadata_types)
    for field in copyfield:
        imagelistmetadata[field] = dictionary[field]
    for field in time_required_metadata:
        stringform = dictionary[field]
        imagelistmetadata[field] = datetime.datetime(*(time.strptime(stringform, time_format_definition)[0:7]))
    # Now we generate the output
    output = ListModel(metadata = imagelistmetadata,
        endorser = endorser,
        images = allimages
        )
    return output


def VMimageListDecoderHeader(dct):
    if not u'hv:imagelist' in dct.keys():
        return None
    dictionary = dct[u'hv:imagelist']
    if not isinstance(dictionary, dict):
        return None
    return VMimageListDecoder(dictionary)
    
def file_extract_metadata(file_name):
    if file_name == None:
        return
    if not os.path.isfile(file_name):
        return None
    m = hashlib.sha512()
    filelength = 0
    for line in open(file_name,'r'):
        filelength += len(line)
        m.update(line) 
    return {u'hv:size' : filelength, 
            u'sl:checksum:sha512' : m.hexdigest()}



class VMListView:
    def __init__(self):
        self.logger = logging.getLogger("hepixvmitrust.vmitrustlib.VMListView")
        
    def load_file(self,filename):
        loadedfile = None
        fp = open(filename, 'r')
        loadedfile = json.load(fp)
        decoded_image = VMimageListDecoderHeader(loadedfile)
        if decoded_image != None:
            return decoded_image
        else:
            decoded_image = VMimageListDecoder(loadedfile)
            if decoded_image != None:
                # This should be upgraded to a Warning after release 0.10
                self.logger.info("Parsing depricated hepiximagelist format.")
                return decoded_image
            else:
                self.logger.warning("This code must be removed soon.")
        self.logger.error("Failed to parse hepiximagelist format.")
        return decoded_image
        
    def save_file(self,entry,filename):
        f = open(filename, 'w')
        json.dump(entry, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
        return True
    def images_list(self,entry):
        #print "frod=%s" % (entry)
        for item in entry.images:
            print item.metadata[u'vmi_uid']
    def images_list(self,entry):
        #print "frod=%s" % (entry)
        for item in entry.images:
            print item.metadata[u'vmi_uid']
    def dumps(self,entry):
        return json.dumps(entry, cls=VMimageListEncoder, sort_keys=True, indent=4)



class VMListControler:
    def __init__(self):
        self.logger = logging.getLogger("hepixvmitrust.vmitrustlib.VMListControler")
        
        self.view = VMListView()
        self.model = ListModel()
    def load(self,filename):
        try:
            candidate = self.view.load_file(filename)
        except ValueError:
            return False
        if candidate == False:
            return False
        self.model = candidate
        return True
        
    def save(self,filename):
        self.view.save_file(self.model,filename)
        
    def images_list(self):
        if self.model == None:
            return False
        return self.view.images_list(self.model)
    def image_add(self,filename):
        f = open(filename, 'r')
        json_stuff = json.load(f)
        fred= VMimageDecoder(json_stuff)
        if fred == None:
            return False
        self.model.images.append(fred)
        return True
        
    def image_del(self,uuid):
        matchuuid = None
        if uuid == 'null':
            matchuuid = None
        else:
            matchuuid = uuid
        todelete = []
        for i in range(len(self.model.images)):
            item = self.model.images[i]
            if item.metadata[u'vmi_uid'] == matchuuid:
                todelete.insert(0, i)
        if len(todelete) == 0:
            return False
        for i in todelete:
            del self.model.images[i]
        return True
        
    def verify(self):
        ### This function verifies the values of the metadata 
        ### 
        if self.model == None:
            return False
        if not imagelist_required_metadata_set.issubset(self.model.metadata.keys()):
            self.logger.error("missing metadata =%s" % ( self.model.metadata.keys()))
            return False
        for item in imagelist_required_metadata:
            value = self.model.metadata[item]
            if value == None or value == "":
                self.logger.error("image list metadata set to none '%s'" % (item))
                return False
        for image in self.model.images:
            for item in image_required_metadata:
                value = image.metadata[item]
                if value == None or value == "":
                    self.logger.error("image metadata set to none '%s'" % (item))
                    return False
        for item in endorser_required_metadata:
            value = self.model.endorser.metadata[item]
            if value == None or value == "":
                self.logger.error("endorser metadata set to none '%s'" % (item))
                return False
        return True
        
    def sign(self,signer_key,signer_cert,outfile):
        content = self.view.dumps(self.model)
        smime = M2Crypto.SMIME.SMIME()
        smime.load_key(signer_key,signer_cert)
        buf = M2Crypto.BIO.MemoryBuffer(content)        
        p7 = smime.sign(buf,M2Crypto.SMIME.PKCS7_DETACHED)
        buf = M2Crypto.BIO.MemoryBuffer(content)
        out = M2Crypto.BIO.MemoryBuffer()
        smime.write(out, p7, buf)
        message_signed = str(out.read())
        f = open(outfile, 'w')
        f.write(message_signed)
        return True

    def generate(self,filename,imagepath=None):
        output_image = None

        if imagepath!=None:

            metadata = file_extract_metadata(imagepath)
            if metadata == None:
                self.logger.error("reading file '%s'." % (imagename))
                return False
            output_image = ImageModel(metadata=metadata)
        else:
            output_image = ImageModel()
        f = open(filename, 'w')
        json.dump(output_image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
        return True
