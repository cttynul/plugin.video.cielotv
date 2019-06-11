#!/usr/bin/python
import os, re, subprocess, sys, xbmcplugin
from datetime import timedelta#, datetime
from lib import neverwise

class Main(object):

  USER_AGENT = "okhttp/3.3.0"
  _handle = int(sys.argv[1])
  _params = neverwise.urlParametersToDict(sys.argv[2])
  _access_token = None

  def __init__(self):
    fanart = neverwise.addon.getAddonInfo('fanart')

    if len(self._params) == 0:
      # cielo
      # using isplayable = true cause kodi/xbmc can handle m3u8 streaming
      response = self._getResponseJson('https://video.sky.it/be/getLivestream?id=2')
      url = response.body["streaming_url"]
      self._addItem(title="cielo", url=url, logo="", fanart="", plot="", duration="", isPlayable=True)
      response = self._getResponseJson('https://video.sky.it/be/getLivestream?id=7')
      url = response.body["streaming_url"]
      self._addItem(title="tv8", url=url, logo="", fanart="", plot="", duration="", isPlayable=True)
      response = self._getResponseJson('https://video.sky.it/be/getLivestream?id=1')
      url = response.body["streaming_url"]
      self._addItem(title="tg 24", url=url, logo="", fanart="", plot="", duration="", isPlayable=True)
      xbmcplugin.endOfDirectory(self._handle)
    else:
      pass

  def _getResponseJson(self, url, add_bearer = False):
    response = neverwise.getResponseJson(url, self._getHeaders(add_bearer), False)
    return response

  def _getHeaders(self, add_bearer = False):
    default_headers = { 'User-Agent' : Main.USER_AGENT, 'Accept-Encoding' : 'gzip' }
    headers = None
    if self._access_token != None:
      headers = { 'AccessToken' : self._access_token }
      for key, value in default_headers.iteritems():
        headers[key] = value
    if headers == None:
      headers = default_headers
    return headers

  def _getVideoInfo(self, video, time_zone = None):
    title = u'{0} ({1} {2} - {3} {4})'.format(video['Name'], neverwise.getTranslation(30011), video['SeasonNumber'], neverwise.getTranslation(30012), video['EpisodeNumber'])
    descr = video['Description']
    if 'PublishEndDate' in video:
      if time_zone == None:
        time_zone = neverwise.gettzlocal()
      date = neverwise.strptime(video['PublishEndDate'], '%Y-%m-%dT%H:%M:%SZ')
      date = date.replace(tzinfo = neverwise.gettz('UTC'))
      date = date.astimezone(time_zone)
      descr = u'{0}\n\n{1} {2}'.format(descr, neverwise.getTranslation(30013), date.strftime(neverwise.datetime_format))
    return { 'img' : video['Images'][0]['Src'], 'title' : title, 'descr' : descr }

  def _addItem(self, title, url, logo = 'DefaultFolder.png', fanart = None, plot = None, duration = '', isPlayable = False, contextMenu = None):
    li = neverwise.createListItem(title, thumbnailImage = logo, fanart = fanart, streamtype = 'video', infolabels = { 'title' : title, 'plot' : plot }, duration = duration, isPlayable = isPlayable, contextMenu = contextMenu)
    xbmcplugin.addDirectoryItem(self._handle, url, li, not isPlayable)

  def _getDuration(self, milliseconds):
    return str(timedelta(milliseconds/1000.0))


# Entry point.
#startTime = datetime.now()
main = Main()
del main
