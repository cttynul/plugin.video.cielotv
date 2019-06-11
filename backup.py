'''
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
      response = self._getResponseJson('https://video.sky.it/be/getLivestream?id=2')
      url = response.body["streaming_url"]
      self._addItem("cielo", url, "", "", "")
      xbmcplugin.endOfDirectory(self._handle)
    else:
      pass
      self._access_token = self._params['at']

      if self._params['action'] == 's':
        response = self._getResponseJson('https://dplayproxy.azurewebsites.net/api/Show/GetById/?id={0}'.format(self._params['value']))
        if response.isSucceeded:
          if len(response.body['Sections']) > 0:
            fanart = response.body['Images'][0]['Src']
            time_zone = neverwise.gettzlocal()
            haveFFmpeg = os.path.isfile(neverwise.addon.getSetting('ffmpeg_path')) and os.path.isdir(neverwise.addon.getSetting('download_path'))
            for video in response.body['Sections'][0]['Items']:
              season_number = video['SeasonNumber'] if 'SeasonNumber' in video else '0'
              if 'Episodes' in video:
                for video in video['Episodes']:
                  vd = self._getVideoInfo(video, time_zone)
                  cm = neverwise.getDownloadContextMenu('RunPlugin({0})'.format(neverwise.formatUrl(params)), vd['title']) if haveFFmpeg else None
                  params = { 'at' : self._access_token, 'action' : 'v', 'value' : video['Id'] } #'v' instead of 'd'
                  #params['action'] = 'v'
                  self._addItem(vd['title'], params, vd['img'], fanart, vd['descr'], self._getDuration(video['Duration']), True, cm)
            xbmcplugin.setContent(self._handle, 'episodes')
            xbmcplugin.endOfDirectory(self._handle)
          else:
            neverwise.showNotification(neverwise.getTranslation(30014))

      elif self._params['action'] == 'v':
        result = self._getStream(self._params['value'])
        if not result:
          neverwise.showVideoNotAvailable()
        else:
          # Force XBMC to set the User-Agent HTTP header to the correct value
          result_url = result['url'] + "|User-Agent=%s" % Dplay.USER_AGENT

          neverwise.playStream(self._handle, result['title'], result['img'], result_url,
                        'video', { 'title' : result['title'], 'plot' : result['descr'] })

      elif self._params['action'] == 'd':
        result = self._getStream(self._params['value'])
        if not result:
          neverwise.showVideoNotAvailable()
        else:
          name = ''.join([i if ord(i) < 128 else '' for i in result['title'].replace(' ', '_')])
          name = '{0}.ts'.format(name)
          os.chdir(neverwise.addon.getSetting('download_path'))
          #~ subprocess.call([neverwise.addon.getSetting('ffmpeg_path'), '-i', result['url'], '-c', 'copy', name])
          subprocess.Popen([neverwise.addon.getSetting('ffmpeg_path'), '-user-agent', Dplay.USER_AGENT, '-i', result['url'], '-c', 'copy', name])


  def _getStream(self, video_id):
    result = {}
    response = self._getResponseJson('https://dplayproxy.azurewebsites.net/api/Video/GetById/?id={0}'.format(video_id))
    if response.isSucceeded:
      vd = self._getVideoInfo(response.body)
      result['title'] = vd['title']
      result['descr'] = vd['descr']
      result['img'] = vd['img']
      response = self._getResponseJson('https://dplay-south-prod.disco-api.com/playback/videoPlaybackInfo/{0}'.format(video_id), True)
      if response.isSucceeded:
        url = response.body['data']['attributes']['streaming']['hls']['url']
        stream = neverwise.getResponse(url, headers={"User-Agent": Dplay.USER_AGENT})
        if stream.isSucceeded:
          qlySetting = neverwise.addon.getSetting('vid_quality')
          if qlySetting == '0':
            qlySetting = 180
          elif qlySetting == '1':
            qlySetting = 270
          elif qlySetting == '2':
            qlySetting = 360
          elif qlySetting == '3':
            qlySetting = 432
          elif qlySetting == '4':
            qlySetting = 576
          elif qlySetting == '5':
            qlySetting = 720
          elif qlySetting == '6':
            qlySetting = 1080
          else:
            qlySetting = 576
          strms_names = re.findall('RESOLUTION=.+?x(.+?),.+?".+?"\s(.+)', stream.body)
          items = []
          for qly, strm_name in strms_names:
            items.append(( abs(qlySetting - int(qly)), strm_name.strip() ))
          items = sorted(items, key = lambda item: item[0])
          i_end = url.find('?')
          i_start = url.rfind('/', 0, i_end) + 1
          old_str = url[i_start:i_end]
          result['url'] = url.replace(old_str, items[0][1])
    return result


  def _getResponseJson(self, url, add_bearer = False):

    response = neverwise.getResponseJson(url, self._getHeaders(add_bearer), False)
    return response


  def _getHeaders(self, add_bearer = False):

    default_headers = { 'User-Agent' : Dplay.USER_AGENT, 'Accept-Encoding' : 'gzip' }
    headers = None
    if self._access_token != None:
      headers = { 'AccessToken' : self._access_token }
      for key, value in default_headers.iteritems():
        headers[key] = value
    if headers == None:
      headers = default_headers
    if add_bearer:
      headers['Authorization'] = 'Bearer {0}'.format(self._access_token[0 : self._access_token.index('__!__') - len(self._access_token)])

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
'''