# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import Stream, request


class ir_binary(models.AbstractModel):
    """
    Re-write to process synced attachments binary
    """
    _inherit = "ir.binary"

    def _record_to_stream(self, record, field_name):
        """
        Re-write to process synced attachments that do not have store_fname, are of the URL type
        """
        if record._name == "ir.attachment" and record.cloud_key:
            streamObject = Stream(
                mimetype=record.mimetype, download_name=record.name, conditional=True, etag=record.checksum, type="data"
            )
            raw_content = record.raw
            if raw_content:
               streamObject.data = raw_content
               streamObject.last_modified = record.write_date
               streamObject.size = record.file_size
            else:
                streamObject.data = b""
                streamObject.size = 0
            return streamObject

        return super(ir_binary, self)._record_to_stream(record=record, field_name=field_name)

    def _get_image_stream_from(
        self, record, field_name="raw", filename=None, filename_field="name", mimetype=None,
        default_mimetype="image/png", placeholder=None, width=0, height=0, crop=False, quality=0,
    ):
        """
        Re-write to process synced images as regular attachments since backward synced images do not have
        all required attributes to be processed as regular images
        """
        if record._name == "ir.attachment" and record.cloud_key:
            try:
                stream = self._get_stream_from(record, field_name, filename, filename_field, mimetype, default_mimetype)
                return stream
            except:
                if request.params.get("download"):
                    raise
        return super(ir_binary, self)._get_image_stream_from(
            record=record, field_name=field_name, filename=filename, filename_field=filename_field,
            mimetype=mimetype, default_mimetype=default_mimetype, placeholder=placeholder,
            width=width, height=height, crop=crop, quality=quality
        )

