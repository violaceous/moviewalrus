from functools import partial
import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import redis
import os.path 
 
LISTENERS = []
 
def redis_listener():
    r = redis.Redis()
    ps = r.pubsub()
    ps.subscribe('amazon_spider')
    io_loop = tornado.ioloop.IOLoop.instance()
    for message in ps.listen():
        for element in LISTENERS:
            io_loop.add_callback(partial(element.on_message, message))
 
 
class NewMsgHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
    def post(self):
        data = self.get_argument('data')
        r = redis.Redis()
        r.publish('test_realtime', data)
 
 
class RealtimeHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        LISTENERS.append(self)
 
    def on_message(self, message):
        self.write_message(message['data'])
 
    def on_close(self):
        LISTENERS.remove(self)
 
 
settings = {
    'auto_reload': True,
}

""" 
application = tornado.web.Application([
    (r'/', NewMsgHandler),
    (r'/realtime/', RealtimeHandler),
], settings = dict(template_path=os.path.join(os.path.dirname(__file__), "tornado_templates")), debug=True)
""" 

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', NewMsgHandler),
            (r'/realtime/',RealtimeHandler),
            ]
	settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "tornado_files/templates"),
            static_path=os.path.join(os.path.dirname(__file__), "tornado_files/static"),
            debug=True,
            autoescape=None
        )
        tornado.web.Application.__init__(self, handlers, **settings)
 
if __name__ == "__main__":
    threading.Thread(target=redis_listener).start()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
