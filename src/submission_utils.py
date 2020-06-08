from dataclasses import dataclass


@dataclass
class SubmissionNotification(object):
    id: str
    link_flair_text: str
    permalink: str
    title: str
