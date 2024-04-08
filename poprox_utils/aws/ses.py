import base64
import json
from typing import Union, List, Dict, Optional
from bs4 import BeautifulSoup

import boto3
from botocore import exceptions
from ..exceptions import PoproxAwsUtilitiesException


class Email:
    __DEFAULT_REGION = "us-east-1"

    def __init__(self, session: boto3.Session, region_name: Optional[str] = None):
        self.__session = session
        region_name = region_name if region_name is not None else self.__DEFAULT_REGION
        self._email_client = self.__session.client("ses", region_name=region_name)

    @staticmethod
    def replace_url_to_add_tracking(
        html: str, base_tracking_url: str, parameters: Optional[Dict]
    ) -> str:
        if base_tracking_url is None:
            raise PoproxAwsUtilitiesException("base_tracking_url must be provided")

        if base_tracking_url.endswith("/"):
            base_tracking_url = base_tracking_url[:-1]

        if parameters is None:
            parameters = {}
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.findAll("a", href=True):
            current_parameters = parameters.copy()
            current_parameters.update({"url": a["href"]})
            a["href"] = (
                f"{base_tracking_url}/"
                f"{base64.urlsafe_b64encode(json.dumps(current_parameters).encode('utf-8')).decode('utf-8')}"
            )

        return str(soup)

    @staticmethod
    def extract_parameters_from_url(url: str, base_tracking_url: str) -> Dict:
        if base_tracking_url is None:
            raise PoproxAwsUtilitiesException("base_tracking_url must be provided")

        if not base_tracking_url.endswith("/"):
            base_tracking_url = base_tracking_url + "/"

        encoded = url.replace(base_tracking_url, "")

        return json.loads(base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8"))

    # pylint: disable=too-many-arguments
    def send_email_without_template(
        self,
        email_from: str,
        email_to: Union[str, List[str]],
        subject: str,
        body_html: str,
        track_links: bool = False,
        base_tracking_url: Optional[str] = None,
        parameters: Optional[Dict] = None,
    ):
        """
        Send email without template
        :param email_from:
        :param email_to:
        :param subject:
        :param body_html:
        :param track_links:
        :param base_tracking_url: has to be provided if track_links is True
        :param parameters: Ensure parameters don't contain the key 'url'
        :return:
        """
        if not isinstance(email_to, list):
            email_to = [email_to]

        if base_tracking_url is None and track_links:
            raise PoproxAwsUtilitiesException(
                "base_tracking_url must be provided if track_links is True"
            )

        try:
            if track_links:
                body_html = self.replace_url_to_add_tracking(
                    body_html, base_tracking_url, parameters
                )

            return self._email_client.send_email(
                Source=email_from,
                Destination={"ToAddresses": email_to},
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

    def list_templates(self, max_items: Optional[int] = None):
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
            raise PoproxAwsUtilitiesException(f"Template {template_name} not found") from error

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
