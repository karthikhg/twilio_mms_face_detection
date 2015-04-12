from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
import foscam
import Image
from StringIO import StringIO
import time
import cv2
from twilio.rest import TwilioRestClient
from imgurpython import ImgurClient

faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')


class ImageReadyEvent(QEvent):
  def __init__(self, image):
    QEvent.__init__(self, ImageReadyEventId)
    self._image = image

    def image(self):
      return self._image

class IPCam():
  def __init__(self):
    self.foscam = foscam.FoscamCamera('192.168.1.116:8090', 'admin', 'password')

  def up(self):
    self.direction = self.foscam.UP
    self.foscam.move(self.direction)

  def down(self):
    self.direction = self.foscam.DOWN
    self.foscam.move(self.direction)

  def left(self):
    self.direction = self.foscam.LEFT
    self.foscam.move(self.direction)

  def right(self):
    self.direction = self.foscam.RIGHT
    self.foscam.move(self.direction)

  def stop(self):
    self.foscam.move(self.direction + 1)

  def playVideo(self):
    self.foscam.startVideo(videoCallback, self)

  def stopVideo(self):
    self.foscam.stopVideo()

  def event(self, e):
    if e.type() == ImageReadyEventId:
      data = e.image()
      im = Image.open(StringIO(data))
      self.qim = QImage(im.tostring(), im.size[0], im.size[1], QImage.Format_RGB888)
      self.pm = QPixmap.fromImage(self.qim)
      #self.image_label.setPixmap(self.pm)
      #self.image_label.update()
      with open('picture.png', 'wb') as f:
        f.write(self.pm)
      return 1
    return QWidget.event(self, e)

import numpy as np
def videoCallback(frame, userdata=None):
  nparr = np.fromstring(frame, np.uint8)
  img = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  # detect faces
  faces = faceCascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30,30),
    flags = cv2.cv.CV_HAAR_SCALE_IMAGE
  )
  i = 0
  # draw a rectangle around each face found
  for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    print 'Found face'
    # save the image
    cv2.imwrite('picture.png', img)

    # upload detected image to imgur
    client_id = '<clientid>'
    client_secret = '<client_secret>'
    config = {
      'album': None,
      'name': 'intruder!',
      'title': 'intruder!',
      'description': 'intruder!'
    }
    client = ImgurClient(client_id, client_secret)

    image = client.upload_from_path('picture.png', config=config, anon=False)
    print image['link']

    # Your Account Sid and Auth Token from twilio.com/user/account
    account_sid = "<account_sid>"
    auth_token = "<auth_token>"
    client = TwilioRestClient(account_sid, auth_token)
    message = client.messages.create(body="Intruder Alert!!!",
      to="+15555555555", # Replace with your phone number
      from_="+18008888888",
      media_url=image['link']) # Replace with your Twilio number
    print message.sid

  #with open('picture.png', 'wb') as f:
  #  f.write(img)
  # cv2.imwrite('picture.png', img)

if __name__ == '__main__':
  cam = IPCam()
  cam.playVideo()
  time.sleep(2)
  cam.stopVideo()
  