import unittest

from localstack_client.session import Session

from src.aws import Email
from src.exceptions import PoproxAwsUtilitiesException


class TestEmail(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.email = Email(self.session)

    def test_create_email_template(self):
        template_name = "test"
        try:
            self.email.create_template(
                template_name, "test subject", "<html><body>test</body></html>"
            )
        except PoproxAwsUtilitiesException:
            pass

        # Ensure the template was created
        self.assertTrue(
            any(
                template["Name"] == template_name
                for template in self.email.list_templates()
            )
        )

    def test_update_email_template(self):
        prev_count = len(self.email.list_templates())
        updated_template = {
            "TemplateName": "test",
            "SubjectPart": "test subject changed",
            "HtmlPart": "<html><body>test changed</body></html>",
        }
        self.email.update_template(
            updated_template["TemplateName"],
            updated_template["SubjectPart"],
            updated_template["HtmlPart"],
        )

        # Ensure the number of templates is not changed
        self.assertEqual(prev_count, len(self.email.list_templates()))
        # Ensure the template still exists under the same name
        self.assertTrue(
            any(
                template["Name"] == updated_template["TemplateName"]
                for template in self.email.list_templates()
            )
        )

        response = self.email.get_template(updated_template["TemplateName"])
        # Ensure template was updated
        self.assertEqual(response, updated_template | response)

        # Make sure we can't update a template that doesn't exist
        with self.assertRaises(PoproxAwsUtilitiesException):
            self.email.update_template(
                updated_template["TemplateName"] + "random_name",
                updated_template["SubjectPart"],
                updated_template["HtmlPart"],
            )
