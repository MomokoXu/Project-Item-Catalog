from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

class WebServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            # path variable is provided by BaseHTTPRequestHandler that contains
            # the URL sent by the client to the server as a string.
            if self.path.endswith("/hello"):
                # tell the web server to send a resonse code of 200 indicating
                # successful GET request
                self.send_response(200)
                # send_header fnction here used to indicate that I'm replying
                # with text in the form of HTML to my client.
                self.send_header('Content-type', 'text/html')
                # end_headers fucntion used along with send_header to indicate
                # the end of our HTTP headers int he response.
                self.end_headers()
                # message is the response with some content included to send
                # back to the client.
                # HTML is added to the response output stream
                output = ""
                output += "<html><body>"
                output += "<h1>Hello!</h1>"
                output += '''<form method='POST' enctype='multipart/form-data'
                            action='/hello'><h2>What would you like me to say?
                            </h2><input name="message" type="text" >
                            <input type="submit" value="Submit"> </form>'''
                output += "</body></html>"
                # self.wfile.write function is ued to send a message back to the
                # client
                self.wfile.write(output)
                # print message used for debugging
                print output
                return

            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = ""
                message += "<html><body>&#161Hola!<a href='/hello'> Back to Hello </a></body></html>"
                self.wfile.write(message)
                print message
                return
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                messagecontent = fields.get('message')
            output = ""
            output += "<html><body>"
            output += " <h2> Okay, how about this: </h2>"
            output += "<h1> %s </h1>" % messagecontent[0]
            output += '''<form method='POST' enctype='multipart/form-data'
                        action='/hello'><h2>What would you like me to say?
                        </h2><input name="message" type="text" >
                        <input type="submit" value="Submit"> </form>'''
            output += "</body></html>"
            self.wfile.write(output)
            print output
        except:
            pass

def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print "Web Server running on port %s" % port
        # serve_forever() function keeps server listen constantly
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()