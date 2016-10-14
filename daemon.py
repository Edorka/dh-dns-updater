import simpledaemon
import logging
import time
import requests
import uuid
import ipgetter


class DreamhostDNS():

    def __init__(self, key):
        self.key = key
    
    def list(self, editable=None, record=None,  type=None):
        '''Access to Dreamhost dns-list_records API'''
        params = dict(key=self.key, 
                      uuid=str(uuid.uuid4()), 
                      cmd='dns-list_records',
                      format='json')
        try:
            response = requests.get("https://api.dreamhost.com/", params=params)
        except Exception as e:
            logging.info(e)
            raise e
        if response.ok:
            json = response.json()
            r = json['data']
            if editable is not None:
                r = list(filter((lambda x: x['editable'] == editable), r))
            if record is not None:
                r = list(filter((lambda x: x['record'] == record), r))
            if type is not None:
                r = list(filter((lambda x: x['type'] == type), r))
            return r
        else:
            return None

    def add(self, host, value, type, comment="auto generated"):
        '''Add to Dreamhost dns records'''
        params = dict(key=self.key, uuid=str(uuid.uuid4()), cmd='dns-add_record',
                      format='json', record=host, type=type, value=value, comment=comment)
        try:
            response = requests.get("https://api.dreamhost.com/", params=params)
        except Exception as e:
            logging.info(e)
            raise e
        return response

    def remove(self, record):
        '''Remove from Dreamhost dns records'''
        params = dict(key=self.key, uuid=str(uuid.uuid4()), cmd='dns-remove_record',
                      format='json', record=record.get('record'),
                      type=record.get('type'), value=record.get('value'))
        try:
            response = requests.get("https://api.dreamhost.com/", params=params)
        except Exception as e:
            raise e
        return response


class UpdateDaemon(simpledaemon.Daemon):
    default_conf = './dh-dns.conf'
    section = 'dh-dns'
    can_continue = True

    def run(self):
        api_key = self.config_parser.get(self.section, 'api_key')
        dns_api = DreamhostDNS(api_key)
        domain = self.config_parser.get(self.section, 'domain')
        delay_str = self.config_parser.get(self.section, 'delay')
        delay = int(delay_str)
        last_ip = None
        while self.can_continue:
            current_ip = ipgetter.myip()
            records = dns_api.list(record=domain)
            record = records[0] if len(records) > 0 else None
            configured_ip = record.get('value', None) if record is not None else None
            if record is None or configured_ip is None:
                logging.info('ip needs to be created', current_ip)
                response = dns_api.add(domain, current_ip, 'A')
                logging.info(response.text)           
            elif configured_ip != current_ip:
                logging.info('ip needs to be updated', configured_ip)
                result = dns_api.remove(record)
                response = dns_api.add(domain, current_ip, 'A')
                logging.info(response.text)           
            else:
                logging.info('no need to update')
            last_ip = current_ip 
            time.sleep(delay)
            

if __name__ == '__main__':
    UpdateDaemon().main()
