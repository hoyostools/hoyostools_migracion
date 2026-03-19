/** @odoo-module */
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { onMounted, Component, useRef, onWillUpdateProps } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { WebClient } from "@web/webclient/webclient";
import { useService } from "@web/core/utils/hooks";
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
export class WaveController extends ListController {
   setup() {
       this.orm = useService("orm");
       super.setup();
   }
   async OnTestClick() {
        const configuraciones = await this.orm.search('sale.order', []);
   }
   async pasillo() {
       var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['procesada','=',false]]);
       var proceso = this.orm.call("sale.order", "process_availability", [ids]);
       if(await proceso == true){
            var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['problema','=',false],['procesada','=',false]]);
            this.orm.call("sale.order", "crear_oleadas_pasillo", [ids]);
       }
       await window.location.reload();
   }
   async piso() {
       var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['problema','=',false],['state','not in', ['draft', 'sent', 'cancel']],['procesada','=',false]]);
       this.orm.call("sale.order", "crear_oleadas_piso", [ids]);
       await window.location.reload();
   }
   async turbo() {
   var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['procesada','=',false]]);
       var proceso = this.orm.call("sale.order", "process_availability", [ids]);
       if(await proceso == true){
           var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['problema','=',false],['procesada','=',false]]);
           await this.orm.call("sale.order", "clh_turbo", [ids]);
       }
       await window.location.reload();
   }
   async mkp() {
       var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['procesada','=',false]]);
       var proceso = this.orm.call("sale.order", "process_availability", [ids]);
       if(await proceso == true){
           var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['problema','=',false],['procesada','=',false]]);
           await this.orm.call("sale.order", "clh_mkp", [ids]);
       }
       await window.location.reload();
   }
   async flex() {
       var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['procesada','=',false]]);
       var proceso = this.orm.call("sale.order", "process_availability", [ids]);
       if(await proceso == true){
           var ids = await this.orm.search('sale.order', [['a_procesar', '=', true],['problema','=',false],['procesada','=',false]]);
           await this.orm.call("sale.order", "clh_flex", [ids]);
       }
       await window.location.reload();
   }
}
registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: WaveController,
   buttonTemplate: "sale_ListView_Buttons",
});