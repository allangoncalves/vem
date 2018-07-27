# coding: utf-8
import requests
import json
import time
import urllib
import zipfile
import os
import re
import logging

token = 'f9aeefc6106b2022d58950abeade70da5a3e266d'

headers = {'Authorization': 'token {}'.format(token)}

def get_date(commit_url):
	request = requests.get(commit_url, headers=headers)
	if request.ok:
		content = json.loads(request.content)
		if content:
			return content['commit']['author']['date'].split('T')[0]


def file_from_zip(url, file_name, repository):
	zipname = ''
	urllib.urlretrieve(url, os.path.join(repository, 'temporary'))
	with zipfile.ZipFile(os.path.join(repository, 'temporary'), 'r') as zipdata:
		zipname = re.sub('[\\/:"*?<>|]+', '', zipdata.namelist()[0])
		zipdata.extractall(repository)
	try:
		os.rename(os.path.join(repository, zipname), file_name)
	except WindowsError, e:
		logging.warning('{}'.format(e.strerror))
	os.remove(os.path.join(repository, 'temporary'))
		

def download_releases(user, repository, CONST_MAX=-1):
	##SEND A GET REQUEST FOR THE GITHUB API
	turns = CONST_MAX
	page = 0
	version = 1
	if not os.path.exists(os.path.join('resultados', repository)):
		os.makedirs(os.path.join('resultados', repository))
	while turns != 0:
		page += 1

		request = requests.get('https://api.github.com/repos/'+user+'/'+repository+'/tags',
								headers=headers,
								params={'page': page, 'per_page': 100})
		repository = os.path.join('resultados', repository)
		if request.ok:
			content = json.loads(request.content)
			if content:
				for tag in content:
					commit_date = get_date(tag['commit']['url'])

					file_name = re.sub('[\\/:"*?<>|]+', '', tag['name'])
					file_name = os.path.join(repository, commit_date+'_'+file_name)
					
					
					if os.path.exists(file_name):
						print '{} ja foi baixado'.format(file_name)
						continue
					else:
						print file_name
						try:
							file_from_zip(tag['zipball_url'], file_name, repository)
						except IOError:
							logging.warning('erro na extracao dos arquivos em {}'.format(file_name))
							continue
						version += 1
					turns -= 1
			else:
				return
		else:
			print 'error: '+str(request.status_code)
			return
	else:
		print 'exact amount of tags collected without error'

if __name__ == '__main__':

	import sys
	from repositories import repos

	if not os.path.exists('resultados'):
		os.makedirs('resultados')
	
	if len(sys.argv) < 2:
		for user, repo in repos.iteritems():
			print repo
			download_releases(user, repo)
	elif len(sys.argv) == 3:
		download_releases(sys.argv[1], sys.argv[2])
	elif len(sys.argv) == 4:
		download_releases(sys.argv[1], sys.argv[2], int(sys.argv[3]))
