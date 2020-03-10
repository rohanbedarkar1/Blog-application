from cassandra.cluster import Cluster
cluster = Cluster(['172.17.0.2'])
session = cluster.connect()
session.execute("CREATE KEYSPACE IF NOT EXISTS BlogKeySpace WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }")
session.execute("Create table blogkeyspace.user_by_username (user_name TEXT,  hashed_password TEXT, full_name TEXT, email_id TEXT,  date_created DATE, is_active INT, PRIMARY KEY (user_name))")
session.execute("Create table blogkeyspace.data_by_articleID ( article_id INT, tag_id INT, user_name  TEXT, title TEXT, content TEXT, is_active_article INT, date_created DATE, date_modified DATE, url TEXT, comment_id INT, comment TEXT, timestamp DATE, tag_name TEXT, PRIMARY KEY (article_id)")
Create table data_by_articleID (article_id INT, tag_id INT, user_name  TEXT, title TEXT, content TEXT, is_active_article INT, date_created date, date_modified date, url TEXT, comment LIST<text>, timestamp date, tag_name LIST<text>,  PRIMARY KEY (article_id, user_name));
