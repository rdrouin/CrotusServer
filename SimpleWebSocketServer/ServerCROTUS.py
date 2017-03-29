#  This file contains
#  The MIT License (MIT)
#  Copyright (c) 2013 Dave P.

import signal
import sys
#import ssl
import exceptions

from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer#, SimpleSSLWebSocketServer
#from optparse import OptionParser
import json
import os

debug = 1

class ServerCROTUS(WebSocket):
   sensor = {}
   chair = {}
   website = {}
   unknown = []

   entityDefinition = {"type":"entity_type",
                               "id":"entity_id"}
   alertTemplate = {"zone":"zone",
                    "entity_id":"target_id",
                    "level": "alert_type"}
   entityId = "entity_id"
   entityTypes = {"sensor": sensor,
                  "chair": chair,
                  "website": website}

   lowBatteryTemplate = "lowBattery"
   message_id = "message_id"

  # def __init__(self, sock, address):
   #   print "infant"
     # super(SimpleChat, self).__init__(sock, address, address)
    #  self.connectionHandlerSwitch = {self.connectionTemplate:self.connectionHandler}

   def __init__(self, server, sock, address):
      super(ServerCROTUS, self).__init__(server, sock, address)
      self.connectionHandlerSwitch = {"connection": self.connectionHandler,
                                       "lowBattery":self.lowBatteryHandler,
                                       "alert":self.alertHandler}

   @staticmethod
   def printError():
      exc_type, exc_obj, exc_tb = sys.exc_info()
      fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
      print exc_type, fname, "line:", exc_tb.tb_lineno

   def notifyWebsites(self, t, message):
      msg = ""
      if isinstance(message, str):
         msg = json.loads(u"{\"type\":" + str(type) + u"," +
                       u"\"data\":"+  message + u"}")
      if isinstance(message, dict):
         msg = u"{\"type\":\"" + str(t) + u"\"," + u"\"data\": " + json.dumps(message) + u"}"

      for w in self.website.keys():
         self.website[w].sendMessage(msg)

   def connectionHandler(self, message):
      """
      Handles connection events
      The text format should be like follows
      {"message_id":"connection", "entity_type":"\w+", "entity_id":"\w+"}
      :param message: Dictionnary containing information about the new connection
      """
      assert isinstance(message, dict)
      try:
         if self in self.unknown:
            self.unknown.remove(self)
            self.entityTypes[message[self.entityDefinition["type"]]][
              message[self.entityDefinition["id"]]] = self

            if message[self.entityDefinition["type"]] != "website":
               webMessage = message
               del webMessage[self.message_id]
               print json.dumps(webMessage)
               self.notifyWebsites("connection", webMessage)

            if debug:
               print "connection of new", self.entityNameStr(self)
         else:
            print "Double connection"

      except Exception:
         self.printError()

   def lowBatteryHandler(self, message):
      """
      Handles low battery events
      The text format should be like follows
      {"message_id":"lowBattery"}
      :param message: Dictionnary containing information about the low battery event
      """
      try:
         if self not in self.unknown:
            entityName = self.entityNameStr(self)
            if entityName:
               if debug:
                  print "Warning - A low battery is detected on machine" , self.entityNameStr(self)
            else:
               print "Unregistered person calling"
         else:
            print "Unknown person calling"

      except Exception:
         self.printError()

   def alertHandler(self, message):
      """
      Handles alerts battery events
      The text format should be like follows
      {"message_id":"alert", "alert_type":"\d+", "target_id":"\w+", "zone":"\w+"}
      :param message: Dictionary containing information about the alert event
      """
      try:
         if self not in self.unknown:
            id = self.findEntity(self)
            if id:
               print "Unknown person calling"
               return
            entity_id = self.findEntity(message[self.alertTemplate["entity_id"]], "chair")
            if entity_id:
               if debug:
                  print "Alert", message[self.alertTemplate["level"]], " - " ,\
                     self.entityNameStr(entity_id), \
                     "has entered zone", message[self.alertTemplate["zone"]], "which triggered alert type"
            else:
               print "Unknown trespasser"
         else:
            print "Unknown person calling"

      except Exception:
         self.printError()

   def handleMessage(self):
      try:
         message = json.loads(self.data, None)
         if message[self.message_id] in self.connectionHandlerSwitch:
            self.connectionHandlerSwitch[message[self.message_id]](message)
         else:
            if debug:
               entityName = self.entityName(self)
               print "Not supported message type:", message, "from:", entityName
      except exceptions.ValueError:
            print "Message malformed"
            print self.data
      except Exception:
         self.printError()

   def entityName(self, conn):
      for t in self.entityTypes.keys():
         for k in self.entityTypes[t]:
               if self.entityTypes[t][k] == conn:
                     return {self.entityDefinition["type"]:t,
                             self.entityDefinition["id"]:k}

   def entityNameStr(self, entityName):
      if isinstance(entityName, dict):
         return str(entityName[self.entityDefinition["type"]]) + " " + str(entityName[self.entityDefinition["id"]])
      else:
         ## case is a WebSocketObj
         entityName = self.entityName(entityName)
         return str(entityName[self.entityDefinition["type"]]) + " " + str(entityName[self.entityDefinition["id"]])
         pass

   def removeEntity(self, entity, dictEntities):
      for k in dictEntities:
            if dictEntities[k] == entity:
                  del dictEntities[k]

   def findEntity(self, conn, t = None):
      if not t:
         for t in self.entityTypes.keys():
            for k in self.entityTypes[t].keys():
               if self.entityTypes[t][k] is conn:
                  return self.entityTypes[t][k]
               return None
      else:
         if conn in self.entityTypes[t]:
            return self.entityTypes[t][conn]

   def isType(self, t):
      for k in self.entityTypes[t]:
            #if
         pass

   def handleConnected(self):
      print (self.address, 'connected')
      self.unknown.append(self)
      ## Next line should be in the __init__ but i can't figure out how to pass the correct arguments for super class

   def handleClose(self):
      try:
         for types in self.entityTypes.keys():
            self.removeEntity(self, self.entityTypes[types])
         if self in self.unknown:
            self.unknown.remove(self)
      except Exception as e:
         print type(e)


if __name__ == "__main__":
   server = SimpleWebSocketServer("", 8000, ServerCROTUS)

   def close_sig_handler(signal, frame):
      server.close()
      sys.exit()

   signal.signal(signal.SIGINT, close_sig_handler)

   server.serveforever()
