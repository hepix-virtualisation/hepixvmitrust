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
        self.indent =4
        self.sort_keys = True
    def load_file(self,filename):
        self.logger.warn("Using depricated function 'load_file'")
        loadedfile = None
        fp = open(filename, 'r')
        json_string = fp.read()
        return self.loads(json_string)
        
    def save_file(self,entry,filename):
        f = open(filename, 'w')
        json.dump(entry, f, cls=VMimageListEncoder, sort_keys=self.sort_keys, indent=self.indent)
        return True
        
    def images_list(self,entry):
        for item in entry.images:
            if u'dc:identifier' in item.metadata.keys():
                print item.metadata[u'dc:identifier']
                
    def dumps(self,entry):
        return json.dumps(entry, cls=VMimageListEncoder, sort_keys=self.sort_keys, indent=self.indent)

    def loads(self,json_string):
        loadedfile = json.loads(json_string)
        decoded_image = VMimageListDecoderHeader(loadedfile)
        if decoded_image != None:
            return decoded_image
        else:
            # Hack to get arround imafe format change
            decoded_image = VMimageListDecoder(loadedfile)
            if decoded_image != None:
                # This should be upgraded to a Warning after release 0.10
                self.logger.warning("Parsing depricated hepiximagelist format.")
                return decoded_image
            else:
                self.logger.warning("This code must be removed soon.")
        self.logger.error("Failed to parse hepiximagelist format.")
        return decoded_image
    def enviroment_default_endorser(self,endorser):
        EndorserEnviromentMapping = {'dc:creator' : 'HVMILE_DC_CREATOR',
            'hv:ca' : 'HVMILE_HV_CA',
            'hv:dn' : 'HVMILE_HV_DN',
            'hv:email' : 'HVMILE_HV_EMAIL'}
        endorserkeys = endorser.metadata.keys()
        for metadatakey in EndorserEnviromentMapping.keys():
            needToDefault = False
            if not metadatakey in endorserkeys:
                needToDefault = True
            else:
                CurrentValue = endorser.metadata[metadatakey]
                if CurrentValue == None or CurrentValue == '':
                    needToDefault = True
            if needToDefault:
                env_var = str(EndorserEnviromentMapping[metadatakey])
                newvalue = os.getenv(env_var)
                if newvalue != None:
                    endorser.metadata[metadatakey] = newvalue
        return True
    def enviroment_default_image(self,image):
        ImageEnviromentMapping = {'dc:description' : 'HVMILI_DC_DESCRIPTION',
            'dc:identifier' : 'HVMILI_DC_IDENTIFIER',
            'dc:title' : 'HVMILI_DC_TITLE',
            'hv:hypervisor' : 'HVMILI_HV_HYPERVISOR',
            'hv:size' : 'HVMILI_HV_SIZE',
            'hv:uri' : 'HVMILI_HV_URI',
            'hv:version' : 'HVMILI_HV_VERSION',
            'sl:arch' : 'HVMILI_SL_ARCH',
            'sl:checksum:sha512' : 'HVMILI_SL_CHECKSUM_SHA512',
            'sl:comments' : 'HVMILI_SL_COMMENTS',
            'sl:os' : 'HVMILI_SL_OS',
            'sl:osversion' : 'HVMILI_SL_OSVERSION'}
        imagekeys = image.metadata.keys()
        for metadatakey in ImageEnviromentMapping.keys():
            needToDefault = False
            if not metadatakey in imagekeys:
                needToDefault = True
            else:
                CurrentValue = image.metadata[metadatakey]
                if CurrentValue == None or CurrentValue == '':
                    needToDefault = True
            if needToDefault:
                env_var = str(ImageEnviromentMapping[metadatakey])
                newvalue = os.getenv(env_var)
                if newvalue != None:
                    image.metadata[metadatakey] = newvalue
        return True
    def enviroment_default_imagelist(self,image_list):
        ListEnviromentMapping = {'dc:date:created' : 'HVMIL_DC_DATE_CREATED',
            'dc:date:expires' : 'HVMIL_DC_DATE_EXPIRES',
            'dc:description' : 'HVMIL_DC_DESCRIPTION',
            'dc:identifier' : 'HVMIL_DC_IDENTIFIER',
            'dc:source' : 'HVMIL_DC_SOURCE',
            'dc:title' : 'HVMIL_DC_TITLE',
            'hv:uri' : 'HVMIL_HV_URI',
            'hv:version' : 'HVMIL_HV_VERSION'}
        imagelistkeys = image_list.metadata.keys()
        for metadatakey in ListEnviromentMapping.keys():
            needToDefault = False
            if not metadatakey in imagelistkeys:
                needToDefault = True
            else:
                CurrentValue = image_list.metadata[metadatakey]
                if CurrentValue == None or CurrentValue == '':
                    needToDefault = True
            if needToDefault:
                env_var = str(ListEnviromentMapping[metadatakey])
                newvalue = os.getenv(env_var)
                if newvalue != None:
                    image_list.metadata[metadatakey] = newvalue
        self.enviroment_default_endorser(image_list.endorser)
        for imageIndex in range(len(image_list.images)):
            self.enviroment_default_image(image_list.images[0])
        return True
                
        
        
            
        

class VMListControler:
    def __init__(self):
        self.logger = logging.getLogger("hepixvmitrust.vmitrustlib.VMListControler")        
        self.view = VMListView()
        self.model = ListModel()

    def loaddep(self,filename):
        '''Please use loads
            This function is depricated as its names not clear 
            what it does and its mixed function.
        '''
        self.logger.warn("Using depricated function 'loaddep'")
        f = open(filename, 'r')
        encoding_string = f.read()
        self.loads(encoding_string)
        
    def loads_smime(self,smime_string):
        buf = M2Crypto.BIO.MemoryBuffer(str(smime_string))
        try:
            p7, data = M2Crypto.SMIME.smime_load_pkcs7_bio(buf)
        except AttributeError, e:
            raise e
        self.loads(data.read())
        
    def loads(self,encoding_string):
        try:
            candidate = self.view.loads(str(encoding_string))
        except ValueError:
            self.logger.error("Failed to parse JSON.")
            return False
        if candidate == None:
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
        if not os.path.isfile(filename):
            self.logger.error("Invalid path to file '%s'." % (filename))
            return False
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
            if item.metadata[u'dc:identifier'] == matchuuid:
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
        self.logger.warn("Using depricated function 'sign'")
        self.logger.debug("please dumps and use cryptography in an seperate area.")
        content = self.dumps()
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
                self.logger.error("reading file '%s'." % (imagepath))
                return False
            output_image = ImageModel(metadata=metadata)
        else:
            self.logger.error("geenrating'%s'." % (filename))
            output_image = ImageModel()
        self.view.enviroment_default_image(output_image)
        f = open(filename, 'w')
        json.dump(output_image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
        return True
    def generates(self,filename,imagepath=None,metadata=None):
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
    def dumps(self):
        return self.view.dumps(self.model)
    def enviroment_default(self):
        return self.view.enviroment_default_imagelist(self.model)
