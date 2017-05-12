from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

class WebServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            ########### List of restaurants #########
            # path variable is provided by BaseHTTPRequestHandler that contains
            # the URL sent by the client to the server as a string.
            if self.path.endswith("/restaurants"):
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
                # get all restaurants
                restaurants = session.query(Restaurant).all()
                output = ""
                output += "<html><body>"
                output += "<h1>Hello!</h1><h2>Here is the list of restaurants:</h2><br><br><br>"
                for restaurant in restaurants:
                    output += str(restaurant.id) + " " + restaurant.name
                    output += "<br><br>"
                    output += "<a href = '/restaurants/%s/edit'>Edit</a> " % restaurant.id
                    output += "<a href = '/restaurants/%s/delete'>Delete</a>" % restaurant.id
                    output += "<br><br><br>"
                output += "</body></html>"
                # self.wfile.write function is ued to send a message back to the
                # client
                self.wfile.write(output)
                # print message used for debugging
                # print output
                return

            ####### Create a new Restaurant ########
            if self.path.endswith("/restaurants/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<html><body>"
                output += "<h1>Make a New Restaurant</h1>"
                output += '''<form method = 'POST' enctype='multipart/form-data'
                            action = '/restaurants/new'>
                            <input name = 'newRestaurantName' type = 'text'
                            placeholder = 'New Restaurant Name' >
                            <input type='submit' value='Create'>'''
                output += "</form></body></html>"
                self.wfile.write(output)
                return

            ###### Edit a Restaurant #####
            if self.path.endswith("/edit"):
                restaurantID = self.path.split("/")[2]
                restaurantQuery = session.query(Restaurant).filter_by(id=restaurantID).one()
                if restaurantQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<h1>Make a change for %s</h1>" % restaurantQuery.name
                    output += '''<form method = 'POST' enctype='multipart/form-data'
                                action = '/restaurants/%s/edit'>''' % restaurantID
                    output += '''<input name = 'newRestaurantName' type = 'text'
                                placeholder = '%s' >
                                <input type='submit' value='Rename'>''' % restaurantQuery.name
                    output += "</form></body></html>"
                    self.wfile.write(output)
                    #print output
                    return

            ###### Delete  a Restaurant #####
            if self.path.endswith("/delete"):
                restaurantID = self.path.split("/")[2]
                restaurantQuery = session.query(Restaurant).filter_by(id=restaurantID).one()
                if restaurantQuery:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = ""
                    output += "<html><body>"
                    output += "<h1>Are you sure to delete %s ?</h1>" % restaurantQuery.name
                    output += '''<form method = 'POST' enctype='multipart/form-data'
                                action = '/restaurants/%s/delete'>''' % restaurantID
                    output += "<input name = 'Quit' type='submit' value='Quit'></form>"
                    output += '''<form method = 'POST' enctype='multipart/form-data'
                                action = '/restaurants/%s/delete'>''' % restaurantID
                    output += '''<input name = 'Delete' type='submit' value='Delete'>'''
                    output += "</form></body></html>"
                    self.wfile.write(output)
                    #print output
                    return
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/restaurants/new"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')

                    # Create new Restaurant Object
                    newRestaurant = Restaurant(name=messagecontent[0])
                    session.add(newRestaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurants')
                    self.end_headers()

            if self.path.endswith("/edit"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')
                    for f in fields:
                        print f
                    # Update restaurant object
                    restaurantID = self.path.split("/")[2]
                    restaurantQuery = session.query(Restaurant).filter_by(
                        id=restaurantID).one()
                    if restaurantQuery:
                        restaurantQuery.name = messagecontent[0]
                        session.add(restaurantQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/restaurants')
                        self.end_headers()

            if self.path.endswith("/delete"):
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    if fields.get('Quit'):
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/restaurants')
                        self.end_headers()
                        return
                    # Delete restaurant object
                    restaurantID = self.path.split("/")[2]
                    restaurantQuery = session.query(Restaurant).filter_by(
                        id=restaurantID).one()
                    if restaurantQuery and fields.get('Delete'):
                        session.delete(restaurantQuery)
                        session.commit()
                        self.send_response(301)
                        self.send_header('Content-type', 'text/html')
                        self.send_header('Location', '/restaurants')
                        self.end_headers()
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