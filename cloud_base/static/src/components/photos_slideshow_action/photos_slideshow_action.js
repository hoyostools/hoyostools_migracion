/** @odoo-module **/

import { PhotosSlideShow } from "@cloud_base/components/photos_slideshow/photos_slideshow";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useState } = owl;


export class PhotosSlideShowAction extends Component {
    static template = "cloud_base.PhotosSlideShowContainer";
    static components = { PhotosSlideShow };
    static props = { ... standardActionServiceProps };
    /*
    * Re-write to introduce our own services and props
    */
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({ images: []});
        onWillStart(async () => {
            await this._onLoadAttachments(this.props);
        });
    }
    /*
    * The method to go through attachments and leave only ones that are images
    */
    async _onLoadAttachments(props) {
        const attachments = props.action.context.default_attachment_ids ? props.action.context.default_attachment_ids[0][2] : [];
        const images = await this.orm.call("ir.attachment", "action_get_images", [attachments])
        this.state.images = images;
    }
    /*
    * The method to close the action
    * We just get to the previous breadcrumb
    */
    async _onFinishAction() {
        if (this.env.config.breadcrumbs.length > 1) {
            await this.action.restore();
        }
        else {
            await this.action.doAction("cloud_base.ir_attachment_action");
        }
    }
    /*
    * The method to prepare slideshow props
    */
    getPhotosSlideShowProps() {
        return {
            images: this.state.images,
            close: this._onFinishAction.bind(this),
        };
    }
}


registry.category("actions").add("photos.slide.show", PhotosSlideShowAction);

