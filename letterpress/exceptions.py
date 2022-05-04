class ElasticsearchException(Exception):
    """
    Exception that's specific for Elasticsearch

    status is Http status, if relevant
    """

    def __init__(self, status, error):
        self.status = status
        self.error = error
        super().__init__(self.error)
