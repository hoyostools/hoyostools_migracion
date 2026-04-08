/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
const { Component, onMounted, useState } = owl;
const preloadNum = 3;


export class PhotosSlideShow extends Component {
    static template = "cloud_base.PhotosSlideShow";
    static props = {
        images: { type: Array },
        close: { type: Function, optional: true },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({
            preLoadedImages: [],
            loadedImages: [],
            currentIndex: 0,
            playing: true,
            speed: 5000,
        });
        onMounted(async () => {
            this.photosContainer = $(".cb-photos-container");
            this.controlElements = $(".cb-photos-control-elements");
            await this._onSelectImage();
            this._onStartSliding();
            this._onFocus();
            this._onActivateControlPanel();
        });
    }
    /*
    * The method to create an image element and all its linked events
    */
    _onLoadImage(currentIndex) {
        if (!(this.state.preLoadedImages.includes(currentIndex))) {
            var self = this;
            const imgElement = document.createElement("img");
            imgElement.id = "cb-photo-img-" + currentIndex;
            imgElement.src = this.props.images[currentIndex];
            imgElement.classList.add("h-100", "cb-photo-current");
            const wheelElement = document.createElement("div");
            wheelElement.classList.add("cb-photo-current", "cb-photo-wheel", "h-100", "flex-column-reverse", "d-flex");
            wheelElement.id = "cb-photo-wheel-" + currentIndex;
            const wheelElementIcon = document.createElement("i");
            wheelElementIcon.classList.add("fa", "fa-3x", "fa-circle-o-notch", "fa-fw", "fa-spin", "text-white");
            wheelElementIcon.role = "img";
            wheelElement.prepend(wheelElementIcon);
            this.photosContainer[0].prepend(imgElement);
            this.photosContainer[0].prepend(wheelElement);
            imgElement.addEventListener("error", function (event) {
                event.target.src = "/web/static/img/placeholder.png";
            });
            imgElement.addEventListener("load", function (event) {
                const checkedItem = parseInt(event.target.id.substring(13));
                $("#cb-photo-wheel-" + checkedItem).remove();
                self.state.loadedImages.push(checkedItem);
                if (self.state.currentIndex == checkedItem) {
                    self._showImg();
                    self._onStartSliding();
                };
            });
            this.state.preLoadedImages.push(currentIndex);
        };
    }
    /*
    * The method to select the current & to load predecessors and its descendants (so, images are switched smoothly)
    */
    async _onSelectImage() {
        let currentIndex = this.getPreviousIndex(this.state.currentIndex - preloadNum);
        let preloadIndex = 0;
        while (preloadIndex < preloadNum*2 + 1) {
            this._onLoadImage(currentIndex);
            currentIndex = this.getNextIndex(currentIndex);;
            preloadIndex += 1;
        };
        this._showImg();
    }
    /*
    * The method to show the current image or its loading wheel
    */
    _showImg() {
        $(".cb-photo-current").addClass("cb-photos-hidden");
        $("#cb-photo-img-" + this.state.currentIndex).removeClass("cb-photos-hidden");
        $("#cb-photo-wheel-" + this.state.currentIndex).removeClass("cb-photos-hidden");
    }

    /*
    * The method to (re)start sliding after the switch
    */
    async _onStartSliding() {
        var self = this;
        if (this.sliderTimeout) {
           browser.clearTimeout(this.sliderTimeout);
        };
        if (this.state.playing && this.state.loadedImages.includes(this.state.currentIndex)) {
            this.sliderTimeout = browser.setTimeout(async function() {
                await self.next();
            }, this.state.speed);
        };
    }
    /*
    * The method to switch to the next image
    */
    async next() {
        this.state.currentIndex = this.getNextIndex(this.state.currentIndex);
        await this._onSelectImage();
        await this._onStartSliding();
    }
    /*
    * The method to switch to the prvious image
    */
    async previous() {
        this.state.currentIndex = this.getPreviousIndex(this.state.currentIndex);
        await this._onSelectImage();
        await this._onStartSliding();
    }

    /*
    * The next event
    */
    async _onClickNext(event) {
        await this.next();
        this._onFocus();
    }
    /*
    * The previous event
    */
    async _onClickPrevious(event) {
        await this.previous();
        this._onFocus();
    }
    /*
    * The method to pause/start the slideshow
    */
    async _onTogglePlay() {
        this.state.playing = !this.state.playing;
        await this._onStartSliding();
        this._onActivateControlPanel();
    }
    /*
    * The method to get the next index
    */
    getNextIndex(currentIndex) {
        currentIndex = currentIndex + 1;
        if (currentIndex >= this.props.images.length) {
            currentIndex = 0
        };
        return currentIndex
    }
    /*
    * The method to get the previous index
    */
    getPreviousIndex(currentIndex) {
        currentIndex = this.state.currentIndex - 1;
        if (currentIndex < 0) {
            currentIndex = this.props.images.length - 1;
        };
        return currentIndex
    }
    /*
    * The method to change the speed
    */
    async _onChangeSpeed(event) {
        this.state.speed = 1000 * parseInt(event.currentTarget.value);
        await this._onStartSliding();
    }
    /*
    * The method to focus on the main container to listen for keydowns
    */
    _onFocus() {
        this.photosContainer.focus();
    }
    /*
    * The method to activate the control panel
    */
    _onActivateControlPanel() {
        var self = this;
        if (this.moveDebounceTimer) {
            browser.clearTimeout(this.moveDebounceTimer);
        };
        this.moveDebounceTimer= setTimeout(function() {
            self.controlElements.removeClass("cb-photos-hidden");
            if (self.controlTimeout) {
                browser.clearTimeout(self.controlTimeout);
            };
            self.controlTimeout = browser.setTimeout(async function() {
                self._onHideControlPanel();
            }, 5000);
        }, 10);
    }
    /*
    * The method to deactivate the control panel
    */
    _onHideControlPanel() {
        if (this.moveDebounceTimer) {
            clearTimeout(this.moveDebounceTimer);
        };
        this.controlElements.addClass("cb-photos-hidden");
    }
    async close() {
        if (this.props.close) {
            await this.props.close();
        }
        else {
            this.__owl__.remove();
        }
    }
    /*
    * The method to catch keyboard presses
    */
    onKeydown(ev) {
        switch (ev.key) {
            case "Enter":
                this.next();
                break;
            case "ArrowRight":
                this.next();
                break;
            case "ArrowLeft":
                this.previous();
                break;
            case " ":
                this._onTogglePlay();
                break;
            case "Escape":
                this.close();
                break;
            case "q":
                this.close();
                break;
        };
    }
}

