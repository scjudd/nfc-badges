#!/usr/bin/env python

# These are NTAG213 cards.
# http://www.nxp.com/documents/data_sheet/NTAG213_215_216.pdf
# http://www.cardwerk.com/smartcards/smartcard_standard_ISO7816-4_6_basic_interindustry_commands.aspx#chap6_5

import struct
import usb.core


class CCID(object):

    PACKET_LEN = 64

    def __init__(self, dev, read_endpoint=0x81, write_endpoint=0x01):
        self.dev = dev
        self.read_endpoint = read_endpoint
        self.write_endpoint = write_endpoint
    
    def PC_to_RDR_XferBlock(self, data):
        data_len = len(data)
        raw = struct.pack('<BI5B' + 'B' * data_len, 0x6f, data_len, 0, 0, 0, 0, 0, *data)
        self.dev.write(endpoint=self.write_endpoint, data=raw)
        return self.dev.read(self.read_endpoint, CCID.PACKET_LEN)


class Reader(CCID):

    def __init__(self, *args, **kwargs):
        return super(Reader, self).__init__(*args, **kwargs)

    def read_binary(self, page_num, num_bytes=4):
        data = [0xff, 0xb0, 0x00, page_num, num_bytes]
        return self.PC_to_RDR_XferBlock(data)

    def update_binary(self, starting_page, data):
        data = [0xff, 0xd6, 0x00, starting_page, len(data)] + data
        return self.PC_to_RDR_XferBlock(data)

    def get_uid(self):
        data = [0xff, 0xca, 0x00, 0x00, 0x00]
        return self.PC_to_RDR_XferBlock(data)


class NTAG213(object):

    @staticmethod
    def pwd_auth(rdr, pwd):
        data = [0xff, 0x00, 0x00, 0x00, 0x05, 0x1b] + pwd
        print ':'.join('{:02x}'.format(c) for c in data)
        return rdr.PC_to_RDR_XferBlock(data)


def resp_payload(resp):
    return ':'.join('{:02x}'.format(c) for c in resp[10:len(resp)-2])


dev = usb.core.find(idVendor=0x72f, idProduct=0x223b)

if dev is None:
    raise ValueError('Device not found')

try:
    dev.detach_kernel_driver(0)
except:
    pass

dev.set_configuration()

try:
    dev.set_interface_altsetting(0)
except:
    pass

rdr = Reader(dev)
#bytes = NTAG213.pwd_auth(rdr, [0xff]*4)
#print 'auth resp:\t%s' % ':'.join('{:02x}'.format(c) for c in bytes[10:])

#rdr.update_binary(16, [0]*8)
#
#bytes = rdr.update_binary(41, [
#    0x04, 0x00, 0x00, 0xff,
#    0x00, 0x05, 0x00, 0x00,
#    0xff, 0xff, 0xff, 0xff,
#    0x00, 0x00, 0x00, 0x00,
#])
#print ':'.join('{:02x}'.format(c) for c in bytes)
#
#rdr.update_binary(6, [0]*8)
#rdr.update_binary(9, [0]*4)

print '-- UID:\t%s' % resp_payload(rdr.get_uid())
print

print '== User memory pages:'
for i in range(4, 40):
    print '%02d:\t%s' % (i, resp_payload(rdr.read_binary(i)))
print

print '== Dynamic lock bytes:'
resp = rdr.read_binary(0x28)
resp = resp[:13] + resp[14:]
print '%02d:\t%s' % (0x28, resp_payload(resp)+':XX')
print


print '== Configuration pages:'
print '%02d:\t%s' % (0x29, resp_payload(rdr.read_binary(0x29)))
print '%02d:\t%s' % (0x2a, resp_payload(rdr.read_binary(0x2a)))
print '%02d:\t%s' % (0x2b, resp_payload(rdr.read_binary(0x2b)))
print '%02d:\t%s' % (0x2c, resp_payload(rdr.read_binary(0x2c)))
