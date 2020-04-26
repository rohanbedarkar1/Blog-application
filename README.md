# WebBackEnd3
The goal of this project is to design and develop 4 scalable microservices 



## Microservices
There are 4 microservies, each having appropriate JSON data formats, HTTP methods, URL endpoints, and HTTP status codes for each service.

- In version 1.0 of this project, its having a single SQLite database shared by all four microservices. While this architecture is viable when all services are running on a single development machine, it makes it difficult to run the services independently: either all services must remain on a single vertically-scaled server, or they must share access to a remote database server.

- The problem with this appraoch, its harder to scale. To overcome this problem we used cassandra (A NoSQL database). We used the cassandra flask extension to make the connection. In the datamodel we used the a single keyspace and at least one column family (the Cassandra equivalent of a table). we stored login information in a separate column family, but in general all other microservices should connect to a single column family which will not be normalized.

- In this version we implemetned HTTP caching, we find that front-end concerns impact back-end code. In this case, you will probably have noticed that RSS feeds are rather slow to load, because they need to make requests to multiple backend microservices. Worse, each microservice call requires an extra HTTP call in order to validate the HTTP Basic authentication header. We can address this by implementing HTTP caching.

- For load balancing we used Nginx.



# The Project Team
## Team Members
- Shekhar Palit
- Rohan Bedarkar
## Project Technologies
- Programming Language - Python
- Web Frame Work - Flask
- Load Balancer - Ngnix 
- RSS feeds
- DataBase - Apache Cassandra
