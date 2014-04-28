#!/usr/bin/python

from bs4 import BeautifulSoup
import csv
from multiprocessing import Pool
import logging
import urllib2

CHROME_UA_STRING = ('Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/KRT16M) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                    'Chrome/30.0.0.0 Mobile Safari/537.36')

SAFARI_UA_STRING = ('Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X) '
                    'AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 '
                    'Mobile/11A465 Safari/9537.53')

UA_STRING = SAFARI_UA_STRING


def consume(url):
    logging.info('Consuming ' + url)
    # build requester with mobile Chrome UA string
    request = urllib2.Request(url)
    request.add_header('User-Agent', UA_STRING)
    opener = urllib2.build_opener()
    try:
        # Parse returned HTML and strip out metatags
        soup = BeautifulSoup(opener.open(request, timeout=25).read())
        for tag in soup.find_all(name='meta', attrs={'name': "viewport"}):
            # strip out any whitespace
            content = tag['content'].replace(' ', '')
            logging.debug(content)
            # check for required values
            if ('width=device-width' in content
                    and 'minimum-scale=1.0' in content
                    and 'minimal-ui' in content):
                logging.info('Found match:' + url)
                # NB that this returns true if _any_ viewport tag matches
                return {'url': url, 'magic_viewport': True}
        # Couldn't find the magic in any viewport tag
        logging.info("No match for:" + url)
        return {'url': url, 'magic_viewport': False}
    except Exception:
        logging.info('Failed to process URL: ' + url)


def main():
    logging.basicConfig(level=logging.DEBUG)
    urls = []
    with open('urls-50k.csv') as csvfile:
        reader = csv.DictReader(csvfile, ['url', 'cnt'])
        urls = [row['url'] for row in reader]
        urls = urls[1:]     # strip out header row
    # normalize URL encoding of '://'
    urls = [url.replace('%3A%2F%2F', '://') for url in urls]
    # dedupe
    urls = set(urls)
    pool = Pool(processes=200)
    promise = pool.map_async(consume, urls)
    results = []
    try:
        results = promise.get()
    except KeyboardInterrupt:
        logging.error('Terminating worker pool')
        pool.terminate()
        pool.join()
        return
    print "--ALL RESULTS--"
    print results
    print "--RESULTS THAT MATCH--"
    print [result['url'] for result in results
           if result and result['magic_viewport']]
    print "Number of URLs scanned:", len(urls)
    print "Failed checks", len([True for result in results if not result])
    print "Have it:", len([True for result in results
                           if result and result['magic_viewport']])
    print "Don't have it:", len([False for result in results
                                if result and not result['magic_viewport']])

if __name__ == '__main__':
    main()
