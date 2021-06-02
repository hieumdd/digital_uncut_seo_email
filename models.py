import jinja2


class Report:
    def __init__(self, bq_client):
        self.bq_client = bq_client

    def fetch_client(self):
        query = """
        SELECT client FROM EmailAlert._ext_SEOClientList
        """
        rows = self.bq_client.query(query).result()
        return [row.get("client") for row in rows]

    def create_clients(self, client_names):
        self.clients = [
            Client(client_name, self.bq_client) for client_name in client_names
        ]

    def build(self):
        for client in self.clients:
            client.build()

    def run(self):
        client_names = self.fetch_client()
        self.create_clients(client_names)
        self.build()


class Client:
    def __init__(self, name, bq_client):
        self.client_name = name
        self.bq_client = bq_client

    def fetch_data(self):
        loader = jinja2.FileSystemLoader(searchpath="./queries")
        env = jinja2.Environment(loader=loader)
        template = env.get_template("keywords.sql.j2")
        rendered_query = template.render(client_name=self.client_name)
        rows = self.bq_client.query(rendered_query).result()
        return [dict(row.items()) for row in rows]

    def process_data(self, rows):
        self.improved = [row for row in rows if row["improved"] is True]
        self.dropped = [row for row in rows if row["dropped"] is True]
        self.entered = [row for row in rows if row["entered"] is True]
        self.fallen = [row for row in rows if row["fallen"] is True]
        self.reached = [row for row in rows if row["reached"] is True]

    def build(self):
        rows = self.fetch_data()
        self.process_data(rows)
