import json
from typing import Union, List, Dict

from boto3 import Session


class Email:
    def __init__(self, session: Session):
        self.__session = session
        self._email_client = self.__session.client('ses')

    def send_email_without_template(self, email_from: str, email_to: Union[str, List[str]], subject: str,
                                    body_html: str):
        if not isinstance(email_to, list):
            email_to = [email_to]

        return self._email_client.send_email(
            Source=email_from,
            Destination={
                'ToAddresses': [
                    email_to
                ]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        "Charset": "UTF-8",
                        'Data': body_html
                    }
                }
            }
        )

    def list_templates(self, max_items: int = None):
        templates = []
        if max_items is not None:
            return self._email_client.list_templates(MaxItems=max_items)["TemplatesMetadata"]

        response = self._email_client.list_templates()
        templates.extend(response["TemplatesMetadata"])
        while "NextToken" in response:
            response = self._email_client.list_templates(NextToken=response["NextToken"])
            templates.extend(response["TemplatesMetadata"])
        return templates

    def create_template(self, template_name: str, subject_part: str, body_html: str):
        return self._email_client.create_template(
            Template={
                'TemplateName': template_name,
                'HtmlPart': body_html,
                'SubjectPart': subject_part
            }
        )

    def update_template(self, template_name: str, subject_part: str, body_html: str):
        return self._email_client.update_template(
            Template={
                'TemplateName': template_name,
                'HtmlPart': body_html,
                'SubjectPart': subject_part
            }
        )

    def send_email_with_template(self, template_name: str, email_from: str, email_to: Union[str, List[str]],
                                 template_data: Dict):
        if not isinstance(email_to, list):
            email_to = [email_to]

        return self._email_client.send_templated_email(
            Source=email_from,
            Destination={
                'ToAddresses': [
                    email_to
                ]
            },
            Template=template_name,
            TemplateData=json.dumps(template_data)
        )
