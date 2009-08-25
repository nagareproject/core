from nagare.publishers import socketlibevent

def hello_world(environ, start_response):
    start_response("200 OK", [])
    return ["<html>Hello, world!</html>"]

if __name__ == '__main__':
    socketlibevent.WSGIServer(hello_world, ('localhost', 8080)).run()
