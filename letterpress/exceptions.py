class ElasticsearchException(Exception):
    """
    Exception that's specific for Elasticsearch

    status is Http status, if relevant
    """

    def __init__(self, error, status):
        self.error = error
        self.status = status
        super().__init__(self.error)
