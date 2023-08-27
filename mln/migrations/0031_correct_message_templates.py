from django.db import migrations


def replace_message_template_ids(apps, schema_editor):
    ModuleMessage = apps.get_model("mln", "ModuleMessage")
    for module_message in ModuleMessage.objects.all():
        message_template = module_message.message
        if message_template.body_id == 1:
            message_template.body_id = module_message.module_item_id
            message_template.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mln', '0030_alter_messagebody_easy_replies_and_more'),
    ]

    operations = [
        migrations.RunPython(replace_message_template_ids, reverse_code=migrations.RunPython.noop),
    ]