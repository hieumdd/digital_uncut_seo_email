import jinja2


class Report:
    def __init__(self, bq_client):
        self.bq_client = bq_client

    def fetch_client(self):
        query = """
        SELECT client, client_language, client_region FROM EmailAlert._ext_SEOClientList ORDER BY client, client_language
        """
        rows = self.bq_client.query(query).result()
        return [dict(row.items()) for row in rows]

    def create_clients(self, client_dicts):
        self.clients = [
            Client(
                client_dict["client"],
                client_dict["client_language"],
                client_dict["client_region"],
                self.bq_client,
            )
            for client_dict in client_dicts
        ]

    def build(self):
        for client in self.clients:
            client.build()

    def run(self):
        client_dicts = self.fetch_client()
        self.create_clients(client_dicts)
        self.build()
        self.clients_alert = [
            client for client in self.clients if client.client_alert is True
        ]


class Client:
    def __init__(self, name, language, region, bq_client):
        self.client_name = name
        self.language = language
        self.region = region
        self.bq_client = bq_client

    def fetch_data(self):
        loader = jinja2.FileSystemLoader(searchpath="./queries")
        env = jinja2.Environment(loader=loader)
        template = env.get_template("keywords.sql.j2")
        rendered_query = template.render(
            client_name=self.client_name,
            client_language=self.language,
            client_region=self.region,
        )
        rows = self.bq_client.query(rendered_query).result()
        return [dict(row.items()) for row in rows]

    def process_data(self, rows):
        self.improved = [row for row in rows if row["improved"] is True]
        self.dropped = [row for row in rows if row["dropped"] is True]
        self.entered = [row for row in rows if row["entered"] is True]
        self.fallen = [row for row in rows if row["fallen"] is True]
        self.reached = [row for row in rows if row["reached"] is True]
        self.kws = [
            self.improved,
            self.dropped,
            self.entered,
            self.fallen,
            self.reached,
        ]

    def build(self):
        rows = self.fetch_data()
        self.process_data(rows)
        if sum(len(kws) for kws in self.kws) > 0:
            self.client_alert = True
        else:
            self.client_alert = False
