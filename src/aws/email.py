import json
from typing import Union, List, Dict

import boto3
from botocore import exceptions
from ..exceptions import PoproxAwsUtilitiesException


class Email:
    __DEFAULT_REGION = "us-east-1"

    def __init__(self, session: boto3.Session, region_name: str = None):
        self.__session = session
        region_name = region_name if region_name is not None else self.__DEFAULT_REGION
        self._email_client = self.__session.client("ses", region_name=region_name)

    def send_email_without_template(
        self,
        email_from: str,
        email_to: Union[str, List[str]],
        subject: str,
        body_html: str,
    ):
        if not isinstance(email_to, list):
            email_to = [email_to]

        try:
            return self._email_client.send_email(
                Source=email_from,
                Destination={"ToAddresses": [email_to]},
                Message={
                    "Subject": {"Data": subject},
                    "Body": {"Html": {"Charset": "UTF-8", "Data": body_html}},
                },
            )
        except exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "MessageRejected":
                raise PoproxAwsUtilitiesException(
                    f"Message was rejected: {error.response['Error']['Message']}",
                    errors=error,
                ) from error
            if error.response["Error"]["Code"] == "MailFromDomainNotVerified":
                raise PoproxAwsUtilitiesException(
                    "Domain from which you are sending email is not verified",
                    errors=error,
                ) from error
            if error.response["Error"]["Code"] == "ConfigurationSetDoesNotExist":
                raise PoproxAwsUtilitiesException(
                    "Configuration set not found", errors=error
                ) from error

            raise error

    def list_templates(self, max_items: int = None):
        templates = []
        if max_items is not None:
            return self._email_client.list_templates(MaxItems=max_items)[
                "TemplatesMetadata"
            ]

        response = self._email_client.list_templates()
        templates.extend(response["TemplatesMetadata"])
        while "NextToken" in response:
            response = self._email_client.list_templates(
                NextToken=response["NextToken"]
            )
            templates.extend(response["TemplatesMetadata"])
        return templates

    def create_template(self, template_name: str, subject_part: str, body_html: str):
        try:
            return self._email_client.create_template(
                Template={
                    "TemplateName": template_name,
                    "HtmlPart": body_html,
                    "SubjectPart": subject_part,
                }
            )
        except exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "TemplateNameAlreadyExists":
                raise PoproxAwsUtilitiesException(
                    f"Template {template_name} already exists", errors=error
                ) from error
            if error.response["Error"]["Code"] == "InvalidTemplate":
                raise PoproxAwsUtilitiesException(
                    f"Template {template_name} is invalid", errors=error
                ) from error

            raise error

    def update_template(self, template_name: str, subject_part: str, body_html: str):
        try:
            return self._email_client.update_template(
                Template={
                    "TemplateName": template_name,
                    "HtmlPart": body_html,
                    "SubjectPart": subject_part,
                }
            )
        except exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "TemplateDoesNotExist":
                raise PoproxAwsUtilitiesException(
                    f"Template {template_name} does not exist", errors=error
                ) from error
            if error.response["Error"]["Code"] == "InvalidTemplate":
                raise PoproxAwsUtilitiesException(
                    f"Template {template_name} is invalid", errors=error
                ) from error

            raise error

    def get_template(self, template_name: str):
        try:
            response = self._email_client.get_template(TemplateName=template_name)
            return response["Template"]
        except self._email_client.exceptions.TemplateDoesNotExistException as error:
            raise PoproxAwsUtilitiesException(
                f"Template {template_name} not found"
            ) from error

    def send_email_with_template(
        self,
        template_name: str,
        email_from: str,
        email_to: Union[str, List[str]],
        template_data: Dict,
    ):
        if not isinstance(email_to, list):
            email_to = [email_to]

        try:
            return self._email_client.send_templated_email(
                Source=email_from,
                Destination={"ToAddresses": [email_to]},
                Template=template_name,
                TemplateData=json.dumps(template_data),
            )
        except exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "TemplateDoesNotExist":
                raise PoproxAwsUtilitiesException(
                    f"Template {template_name} not found", errors=error
                ) from error
            if error.response["Error"]["Code"] == "MessageRejected":
                raise PoproxAwsUtilitiesException(
                    f"Message was rejected: {error.response['Error']['Message']}",
                    errors=error,
                ) from error
            if error.response["Error"]["Code"] == "MailFromDomainNotVerified":
                raise PoproxAwsUtilitiesException(
                    "Domain from which you are sending email is not verified",
                    errors=error,
                ) from error
            if error.response["Error"]["Code"] == "ConfigurationSetDoesNotExist":
                raise PoproxAwsUtilitiesException(
                    "Configuration set does not exist", errors=error
                ) from error

            raise error
