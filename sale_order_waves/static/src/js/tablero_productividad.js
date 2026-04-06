/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { onMounted, Component, useRef, onWillUpdateProps } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { WebClient } from "@web/webclient/webclient";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
import { renderToElement, renderToFragment } from "@web/core/utils/render";
import { useEffect } from "@odoo/owl";

export class OwlInformDashboard extends Component {

    static template = 'productivity_dashboard_template';
    static props = ["*"];

    setup() {

        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            valores_empleados: {},
            valores_empleados_selection:{},
            ordenes: '', ordenes_asignar: '',
            ordenes_procesar: '',
            ordenes_procesadas: '',
            cumplimiento:'',
            productos_ordenes:'',
            productos_ordenes_asignar:'',
            productos_ordenes_procesar:'',
            productos_ordenes_procesadas:'',
            cumplimiento_productos:'',
            sumar_ordenes:'',
            sumar_ordenes_asignadas:'',
            sumar_ordenes_procesadas:'',
            sumar_ordenes_procesar:'',
            cumplimiento_valor:'',
            cumplimiento_porcentajes:'',
            disable_custom_date: true,
            selected_date_range: 'all',
            root: false,
            fecha_inicio: false,
            fecha_fin: false,
            });

        onWillStart(async () => {
            const today = luxon.DateTime.now();
            this.state.fecha_inicio = today.startOf("day").toISODate();
            this.state.fecha_fin = today.endOf("day").toISODate();
            await this.calcular_datos();
        });

        onMounted(async () => {
            const today = luxon.DateTime.now();
            this.state.fecha_inicio = today.startOf("day").toISODate();
            this.state.fecha_fin = today.endOf("day").toISODate();
            if (await this.state.valores_empleados.length > 0) {
                await this.construirGraficaEmpleados('chartdiv', await this.state.valores_empleados);
            } else {
                console.warn("No hay empleados para construir la gráfica");
            }
            if (this.state.ordenes > 0) {
                await this.construirGraficaDocumentos(this.state.ordenes, this.state.ordenes_asignar, this.state.ordenes_procesadas, this.state.ordenes_procesar);
            } else {
                console.warn("No hay empleados para construir la gráfica");
            }
            this.initSelectMultiple();
        });

    }

    // Función para inicializar el select múltiple
    initSelectMultiple() {
    const selectElement = document.getElementById("empleado_select");
    const selectElement2 = document.getElementById("empleado_select2");
    const selectedTagsContainer = document.getElementById("selected-tags");

    // Función para agregar empleados seleccionados al segundo select
    const updateSecondSelect = () => {
        const selectedOptions = Array.from(selectElement.selectedOptions);

        selectedOptions.forEach(option => {
            if (option.value && option.value !== 'todos') {
                const option2 = document.createElement("option");
                option2.value = option.value;
                option2.selected = true;
                option2.textContent = option.text;
                selectElement2.appendChild(option2);

            }
            if (option.value === 'todos'){
                var ids = Array.from(selectElement.options)
                .filter(option => option.selected)
                .map(option => option.value);
                this.filtrar(ids);
            }
        });
    };

    // Función para renderizar etiquetas basadas en el segundo select
    const renderTags = () => {
        selectedTagsContainer.innerHTML = ""; // Limpiar contenedor de etiquetas
        const selectedOptions = Array.from(selectElement2.options).filter(option => option.selected);

        selectedOptions.forEach(option => {
            if (option.value && option.value !== 'todos' && !document.querySelector(`.tag[data-value="${option.value}"]`)) {
                const tag = document.createElement("span");
                tag.className = "tag";
                tag.textContent = option.text;
                tag.dataset.value = option.value; // Guardar el valor en un atributo data-value

                // Botón para eliminar la etiqueta
                const removeButton = document.createElement("button");
                removeButton.textContent = "×";
                removeButton.className = "remove-tag";
                removeButton.onclick = () => {
                    option.selected = false; // Deseleccionar en el segundo select
                    selectElement2.removeChild(option); // Eliminar del segundo select
                    renderTags(); // Volver a renderizar etiquetas
                };
                var ids = Array.from(selectElement2.options)
                .filter(option => option.selected)
                .map(option => option.value);

                // Llamar a la función filtrar con los IDs seleccionados
                if (!ids.includes("todos") && ids.length !== 0) {
                    this.filtrar(ids);
                }
                if (ids.includes("todos") && ids.length > 1){
                    var ids = Array.from(selectElement.options)
                    .filter(option => option.selected)
                    .map(option => option.value);
                    this.filtrar(ids);
                }
                tag.appendChild(removeButton);
                selectedTagsContainer.appendChild(tag);
            }
        });
    };

    // Listener para cambios en el primer select (agrega seleccionados al segundo select)
    selectElement.addEventListener("change", updateSecondSelect);

    // Listener para cambios en el segundo select (actualiza etiquetas)
    selectElement.addEventListener("change", renderTags);

    // Inicializar el segundo select y etiquetas
    updateSecondSelect();
    renderTags();
}


    captureChange(event){
        var selectedValue = $(event.target).val();
        this.filtrar(selectedValue);
    }

    async filterByDate(ev) {
        const selected = ev.target.value;
        this.state.selected_date_range = selected;
        this.state.disable_custom_date = selected !== "custom";

        const today = luxon.DateTime.now();
        let fechaInicio, fechaFin;

        switch (selected) {
            case "today":
                fechaInicio = today.startOf("day").toISODate();
                fechaFin = today.endOf("day").toISODate();
                break;

            case "this_week":
                fechaInicio = today.startOf("week").toISODate();
                fechaFin = today.endOf("day").toISODate();
                break;

            case "this_month":
                fechaInicio = today.startOf("month").toISODate();
                fechaFin = today.endOf("day").toISODate();
                break;

            case "custom":
                // Si es "custom", no calculamos fechaInicio ni fechaFin aquí.
                return;

            case "all":
                fechaInicio = false;
                fechaFin = false;
        }

        this.state.fecha_inicio = fechaInicio;
        this.state.fecha_fin = fechaFin;

        const numberFormatter = new Intl.NumberFormat('es-ES', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });

        if (fechaInicio && fechaFin)
        {
        var empleados = await this.orm.search('sale.montacargas', [['activo', '=', true],['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
        const datos_empleados_selection = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);
        const empleadosSelection = Object.values(
            datos_empleados_selection.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );

        var ordenes = await this.orm.search('sale.order', [['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        const productos_ordenes = await this.orm.call("sale.order", "contar_productos", [ordenes]);
        const sumar_ordenes = await this.orm.call("sale.order", "sumar_ordenes", [ordenes]);
        this.state.sumar_ordenes = sumar_ordenes;
        this.state.ordenes = ordenes.length;
        this.state.productos_ordenes= productos_ordenes;

        var asignadas = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',false],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_asignar = asignadas.length;
        const productos_ordenes_asignar = await this.orm.call("sale.order", "contar_productos", [asignadas]);
        const sumar_ordenes_asignadas = await this.orm.call("sale.order", "sumar_ordenes", [asignadas]);
        this.state.sumar_ordenes_asignadas = sumar_ordenes_asignadas;
        this.state.productos_ordenes_asignar = productos_ordenes_asignar;

        var procesadas = await this.orm.search('sale.order', [['delivery_status','=','full'],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_procesadas = procesadas.length;
        const productos_ordenes_procesadas = await this.orm.call("sale.order", "contar_productos", [procesadas]);
        const sumar_ordenes_procesadas = await this.orm.call("sale.order", "sumar_ordenes", [procesadas]);
        this.state.sumar_ordenes_procesadas = sumar_ordenes_procesadas;
        this.state.productos_ordenes_procesadas = productos_ordenes_procesadas;

        var procesar = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',true],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_procesar = procesar.length;
        const productos_ordenes_procesar = await this.orm.call("sale.order", "contar_productos", [procesar]);
        const sumar_ordenes_procesar = await this.orm.call("sale.order", "sumar_ordenes", [procesar]);
        this.state.sumar_ordenes_procesar = sumar_ordenes_procesar;
        this.state.productos_ordenes_procesar = productos_ordenes_procesar;

        this.state.cumplimiento = Math.round((this.state.ordenes_procesadas/this.state.ordenes)*100);
        this.state.cumplimiento_productos = Math.round((this.state.productos_ordenes_procesadas/this.state.productos_ordenes)*100);
        this.state.cumplimiento_valor = Math.round((this.state.sumar_ordenes_procesadas/this.state.sumar_ordenes)*100);
        this.state.cumplimiento_porcentajes = Math.round((this.state.cumplimiento+this.state.cumplimiento_productos+this.state.cumplimiento_valor)/3);

        // Formatear los valores antes de asignarlos al estado
        this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
        this.state.sumar_ordenes_asignadas = numberFormatter.format(sumar_ordenes_asignadas);
        this.state.sumar_ordenes_procesadas = numberFormatter.format(sumar_ordenes_procesadas);
        this.state.sumar_ordenes_procesar = numberFormatter.format(sumar_ordenes_procesar);
        const empleados_documentos = this.state.valores_empleados; // Los empleados provienen de las props
        const valoresCalculados = await Promise.all(
            empleados_documentos.map(async (empleado) => {
                const valores =  await this.calcular_documentos(empleado.id, fechaInicio, fechaFin);
                const documentos = await valores[7];
                const productos = await valores[8];
                const valor = numberFormatter.format(await valores[9]);
                const valor_real = await valores[9];
                const cumplimiento = await valores[0];
                const procesado = await valores[1];
                const en_proceso = await valores[2];
                const productos_procesado = await valores[3];
                const productos_en_proceso = await valores[4];
                const valor_procesado = numberFormatter.format(await valores[5]);
                const valor_procesado_real = await valores[5];
                const valor_en_proceso = numberFormatter.format(await valores[6]);
                const cumplimiento_productos = numberFormatter.format(await valores[9]);
                const hora_inicio = numberFormatter.format(await valores[10]);
                const hora_fin = numberFormatter.format(await valores[11]);
                const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                const errores_sobrante = await valores[13];
                const errores_faltante = await valores[14];
                const errores_trocado = await valores[15];
                return { ...empleado, documentos, productos,valor,valor_real,
                    errores_sobrante,
                    errores_faltante,
                    errores_trocado, cumplimiento, tiempo_promedio, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
            })
        );
        const empleadosUnicos = Object.values(
            valoresCalculados.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );
        this.state.valores_empleados = await empleadosUnicos;
        }
        else{

        var empleados = await this.orm.search('sale.montacargas', [['activo', '=', true],['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
        const datos_empleados_selection = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);
        const empleadosSelection = Object.values(
            datos_empleados_selection.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );
        var ordenes = await this.orm.search('sale.order', [['state', 'not in', ['draft', 'sent', 'cancel']]]);
        const productos_ordenes = await this.orm.call("sale.order", "contar_productos", [ordenes]);
        const sumar_ordenes = await this.orm.call("sale.order", "sumar_ordenes", [ordenes]);
        this.state.sumar_ordenes = sumar_ordenes;
        this.state.ordenes = ordenes.length;
        this.state.productos_ordenes= productos_ordenes;

        var asignadas = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',false],['state', 'not in', ['draft', 'sent', 'cancel']]]);
        this.state.ordenes_asignar = asignadas.length;
        const productos_ordenes_asignar = await this.orm.call("sale.order", "contar_productos", [asignadas]);
        const sumar_ordenes_asignadas = await this.orm.call("sale.order", "sumar_ordenes", [asignadas]);
        this.state.sumar_ordenes_asignadas = sumar_ordenes_asignadas;
        this.state.productos_ordenes_asignar = productos_ordenes_asignar;

        var procesadas = await this.orm.search('sale.order', [['delivery_status','=','full'],['state', 'not in', ['draft', 'sent', 'cancel']]]);
        this.state.ordenes_procesadas = procesadas.length;
        const productos_ordenes_procesadas = await this.orm.call("sale.order", "contar_productos", [procesadas]);
        const sumar_ordenes_procesadas = await this.orm.call("sale.order", "sumar_ordenes", [procesadas]);
        this.state.sumar_ordenes_procesadas = sumar_ordenes_procesadas;
        this.state.productos_ordenes_procesadas = productos_ordenes_procesadas;

        var procesar = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',true],['state', 'not in', ['draft', 'sent', 'cancel']]]);
        this.state.ordenes_procesar = procesar.length;
        const productos_ordenes_procesar = await this.orm.call("sale.order", "contar_productos", [procesar]);
        const sumar_ordenes_procesar = await this.orm.call("sale.order", "sumar_ordenes", [procesar]);
        this.state.sumar_ordenes_procesar = sumar_ordenes_procesar;
        this.state.productos_ordenes_procesar = productos_ordenes_procesar;

        this.state.cumplimiento = Math.round((this.state.ordenes_procesadas/this.state.ordenes)*100);
        this.state.cumplimiento_productos = Math.round((this.state.productos_ordenes_procesadas/this.state.productos_ordenes)*100);
        this.state.cumplimiento_valor = Math.round((this.state.sumar_ordenes_procesadas/this.state.sumar_ordenes)*100);
        this.state.cumplimiento_porcentajes = Math.round((this.state.cumplimiento+this.state.cumplimiento_productos+this.state.cumplimiento_valor)/3);

        // Formatear los valores antes de asignarlos al estado
        this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
        this.state.sumar_ordenes_asignadas = numberFormatter.format(sumar_ordenes_asignadas);
        this.state.sumar_ordenes_procesadas = numberFormatter.format(sumar_ordenes_procesadas);
        this.state.sumar_ordenes_procesar = numberFormatter.format(sumar_ordenes_procesar);

        const empleados_documentos = this.state.valores_empleados; // Los empleados provienen de las props
        const valoresCalculados = await Promise.all(
            empleados_documentos.map(async (empleado) => {
                const valores =  await this.calcular_documentos(empleado.id)
                const documentos = await valores[7];
                const productos = await valores[8];
                const valor = numberFormatter.format(await valores[9]);
                const valor_real = await valores[9];
                const cumplimiento = await valores[0];
                const procesado = await valores[1];
                const en_proceso = await valores[2];
                const productos_procesado = await valores[3];
                const productos_en_proceso = await valores[4];
                const valor_procesado = numberFormatter.format(await valores[5]);
                const valor_procesado_real = await valores[5];
                const valor_en_proceso = numberFormatter.format(await valores[6]);
                const cumplimiento_productos = numberFormatter.format(await valores[9]);
                const hora_inicio = numberFormatter.format(await valores[10]);
                const hora_fin = numberFormatter.format(await valores[11]);
                const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                const errores_sobrante = await valores[13];
                const errores_faltante = await valores[14];
                const errores_trocado = await valores[15];
                return { ...empleado, documentos, productos,valor,valor_real,
                    errores_sobrante,
                    errores_faltante,
                    errores_trocado, cumplimiento,tiempo_promedio, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
            })
        );
        const empleadosUnicos = Object.values(
            valoresCalculados.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );
        this.state.valores_empleados = await empleadosUnicos;

        }

        await this.construirGraficaDocumentos(this.state.ordenes, this.state.ordenes_asignar, this.state.ordenes_procesadas, this.state.ordenes_procesar);
        await this.construirGraficaEmpleados('chartdiv', await this.state.valores_empleados);

    }

    async filterByCustomDate(ev) {
        const selectedDate = ev.target.value;
        if (selectedDate) {
            const fechaInicio = ev.target.value;
            const fechaFin = ev.target.value;
            this.state.fecha_inicio = fechaInicio;
            this.state.fecha_fin = fechaFin;
            const numberFormatter = new Intl.NumberFormat('es-ES', {
                style: 'decimal',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            });
            if (fechaInicio && fechaFin)
            {
            var empleados = await this.orm.search('sale.montacargas', [['activo', '=', true], ['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
            const datos_empleados_selection = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);
            const empleadosSelection = Object.values(
                datos_empleados_selection.reduce((acc, empleado) => {
                        const nombre = empleado.user_id[0];

                        if (!acc[nombre]) {
                            // Si el empleado no está en el acumulador, lo agrega.
                            acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                        } else {
                            // Si ya existe, concatena las funciones.
                            acc[nombre].funcion += `, ${empleado.funcion}`;
                        }

                        return acc;
                    }, {})
            );

            var ordenes = await this.orm.search('sale.order', [['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
            const productos_ordenes = await this.orm.call("sale.order", "contar_productos", [ordenes]);
            const sumar_ordenes = await this.orm.call("sale.order", "sumar_ordenes", [ordenes]);
            this.state.sumar_ordenes = sumar_ordenes;
            this.state.ordenes = ordenes.length;
            this.state.productos_ordenes= productos_ordenes;

            var asignadas = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',false],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
            this.state.ordenes_asignar = asignadas.length;
            const productos_ordenes_asignar = await this.orm.call("sale.order", "contar_productos", [asignadas]);
            const sumar_ordenes_asignadas = await this.orm.call("sale.order", "sumar_ordenes", [asignadas]);
            this.state.sumar_ordenes_asignadas = sumar_ordenes_asignadas;
            this.state.productos_ordenes_asignar = productos_ordenes_asignar;

            var procesadas = await this.orm.search('sale.order', [['delivery_status','=','full'],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
            this.state.ordenes_procesadas = procesadas.length;
            const productos_ordenes_procesadas = await this.orm.call("sale.order", "contar_productos", [procesadas]);
            const sumar_ordenes_procesadas = await this.orm.call("sale.order", "sumar_ordenes", [procesadas]);
            this.state.sumar_ordenes_procesadas = sumar_ordenes_procesadas;
            this.state.productos_ordenes_procesadas = productos_ordenes_procesadas;

            var procesar = await this.orm.search('sale.order', [['delivery_status','!=','full'],['delivery_status','!=','full'],['procesada','=',true],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
            this.state.ordenes_procesar = procesar.length;
            const productos_ordenes_procesar = await this.orm.call("sale.order", "contar_productos", [procesar]);
            const sumar_ordenes_procesar = await this.orm.call("sale.order", "sumar_ordenes", [procesar]);
            this.state.sumar_ordenes_procesar = sumar_ordenes_procesar;
            this.state.productos_ordenes_procesar = productos_ordenes_procesar;

            this.state.cumplimiento = Math.round((this.state.ordenes_procesadas/this.state.ordenes)*100);
            this.state.cumplimiento_productos = Math.round((this.state.productos_ordenes_procesadas/this.state.productos_ordenes)*100);
            this.state.cumplimiento_valor = Math.round((this.state.sumar_ordenes_procesadas/this.state.sumar_ordenes)*100);
            this.state.cumplimiento_porcentajes = Math.round((this.state.cumplimiento+this.state.cumplimiento_productos+this.state.cumplimiento_valor)/3);

            // Formatear los valores antes de asignarlos al estado
            this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
            this.state.sumar_ordenes_asignadas = numberFormatter.format(sumar_ordenes_asignadas);
            this.state.sumar_ordenes_procesadas = numberFormatter.format(sumar_ordenes_procesadas);
            this.state.sumar_ordenes_procesar = numberFormatter.format(sumar_ordenes_procesar);
            const empleados_documentos = this.state.valores_empleados; // Los empleados provienen de las props
            const valoresCalculados = await Promise.all(
                empleados_documentos.map(async (empleado) => {
                    const valores =  await this.calcular_documentos(empleado.id, fechaInicio, fechaFin);
                    const documentos = await valores[7];
                    const productos = await valores[8];
                    const valor = numberFormatter.format(await valores[9]);
                    const valor_real = await valores[9];
                    const cumplimiento = await valores[0];
                    const procesado = await valores[1];
                    const en_proceso = await valores[2];
                    const productos_procesado = await valores[3];
                    const productos_en_proceso = await valores[4];
                    const valor_procesado = numberFormatter.format(await valores[5]);
                    const valor_procesado_real = await valores[5];
                    const valor_en_proceso = numberFormatter.format(await valores[6]);
                    const cumplimiento_productos = numberFormatter.format(await valores[9]);
                    const hora_inicio = numberFormatter.format(await valores[10]);
                    const hora_fin = numberFormatter.format(await valores[11]);
                    const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                    const errores_sobrante = await valores[13];
                    const errores_faltante = await valores[14];
                    const errores_trocado = await valores[15];
                    return { ...empleado, documentos, productos,valor,valor_real,
                    errores_sobrante,
                    errores_faltante,
                    errores_trocado, cumplimiento, tiempo_promedio, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
                })
            );
            const empleadosUnicos = Object.values(
                valoresCalculados.reduce((acc, empleado) => {
                        const nombre = empleado.user_id[0];

                        if (!acc[nombre]) {
                            // Si el empleado no está en el acumulador, lo agrega.
                            acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                        } else {
                            // Si ya existe, concatena las funciones.
                            acc[nombre].funcion += `, ${empleado.funcion}`;
                        }

                        return acc;
                    }, {})
            );
            this.state.valores_empleados = await empleadosUnicos;
            }
            else{

            var empleados = await this.orm.search('sale.montacargas', [['activo', '=', true], ['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
            const datos_empleados_selection = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);
            const empleadosSelection = Object.values(
                datos_empleados_selection.reduce((acc, empleado) => {
                        const nombre = empleado.user_id[0];

                        if (!acc[nombre]) {
                            // Si el empleado no está en el acumulador, lo agrega.
                            acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                        } else {
                            // Si ya existe, concatena las funciones.
                            acc[nombre].funcion += `, ${empleado.funcion}`;
                        }

                        return acc;
                    }, {})
            );
            var ordenes = await this.orm.search('sale.order', [['state', 'not in', ['draft', 'sent', 'cancel']]]);
            const productos_ordenes = await this.orm.call("sale.order", "contar_productos", [ordenes]);
            const sumar_ordenes = await this.orm.call("sale.order", "sumar_ordenes", [ordenes]);
            this.state.sumar_ordenes = sumar_ordenes;
            this.state.ordenes = ordenes.length;
            this.state.productos_ordenes= productos_ordenes;

            var asignadas = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',false],['state', 'not in', ['draft', 'sent', 'cancel']]]);
            this.state.ordenes_asignar = asignadas.length;
            const productos_ordenes_asignar = await this.orm.call("sale.order", "contar_productos", [asignadas]);
            const sumar_ordenes_asignadas = await this.orm.call("sale.order", "sumar_ordenes", [asignadas]);
            this.state.sumar_ordenes_asignadas = sumar_ordenes_asignadas;
            this.state.productos_ordenes_asignar = productos_ordenes_asignar;

            var procesadas = await this.orm.search('sale.order', [['delivery_status','=','full'],['state', 'not in', ['draft', 'sent', 'cancel']]]);
            this.state.ordenes_procesadas = procesadas.length;
            const productos_ordenes_procesadas = await this.orm.call("sale.order", "contar_productos", [procesadas]);
            const sumar_ordenes_procesadas = await this.orm.call("sale.order", "sumar_ordenes", [procesadas]);
            this.state.sumar_ordenes_procesadas = sumar_ordenes_procesadas;
            this.state.productos_ordenes_procesadas = productos_ordenes_procesadas;

            var procesar = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',true],['state', 'not in', ['draft', 'sent', 'cancel']]]);
            this.state.ordenes_procesar = procesar.length;
            const productos_ordenes_procesar = await this.orm.call("sale.order", "contar_productos", [procesar]);
            const sumar_ordenes_procesar = await this.orm.call("sale.order", "sumar_ordenes", [procesar]);
            this.state.sumar_ordenes_procesar = sumar_ordenes_procesar;
            this.state.productos_ordenes_procesar = productos_ordenes_procesar;

            this.state.cumplimiento = Math.round((this.state.ordenes_procesadas/this.state.ordenes)*100);
            this.state.cumplimiento_productos = Math.round((this.state.productos_ordenes_procesadas/this.state.productos_ordenes)*100);
            this.state.cumplimiento_valor = Math.round((this.state.sumar_ordenes_procesadas/this.state.sumar_ordenes)*100);
            this.state.cumplimiento_porcentajes = Math.round((this.state.cumplimiento+this.state.cumplimiento_productos+this.state.cumplimiento_valor)/3);

            // Formatear los valores antes de asignarlos al estado
            this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
            this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
            this.state.sumar_ordenes_asignadas = numberFormatter.format(sumar_ordenes_asignadas);
            this.state.sumar_ordenes_procesadas = numberFormatter.format(sumar_ordenes_procesadas);
            this.state.sumar_ordenes_procesar = numberFormatter.format(sumar_ordenes_procesar);

            const empleados_documentos = this.state.valores_empleados; // Los empleados provienen de las props
            const valoresCalculados = await Promise.all(
                empleados_documentos.map(async (empleado) => {
                    const valores =  await this.calcular_documentos(empleado.id)
                    const documentos = await valores[7];
                    const productos = await valores[8];
                    const valor = numberFormatter.format(await valores[9]);
                    const valor_real = valores[9];
                    const cumplimiento = await valores[0];
                    const procesado = await valores[1];
                    const en_proceso = await valores[2];
                    const productos_procesado = await valores[3];
                    const productos_en_proceso = await valores[4];
                    const valor_procesado = numberFormatter.format(await valores[5]);
                    const valor_procesado_real = await valores[5];
                    const valor_en_proceso = numberFormatter.format(await valores[6]);
                    const cumplimiento_productos = numberFormatter.format(await valores[9]);
                    const hora_inicio = numberFormatter.format(await valores[10]);
                    const hora_fin = numberFormatter.format(await valores[11]);
                    const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                    const errores_sobrante = await valores[13];
                    const errores_faltante = await valores[14];
                    const errores_trocado = await valores[15];
                    return { ...empleado, documentos, productos,valor,valor_real,
                    errores_sobrante,
                    errores_faltante,
                    errores_trocado,tiempo_promedio, cumplimiento, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
                })
            );
            const empleadosUnicos = Object.values(
                valoresCalculados.reduce((acc, empleado) => {
                        const nombre = empleado.user_id[0];

                        if (!acc[nombre]) {
                            // Si el empleado no está en el acumulador, lo agrega.
                            acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                        } else {
                            // Si ya existe, concatena las funciones.
                            acc[nombre].funcion += `, ${empleado.funcion}`;
                        }

                        return acc;
                    }, {})
            );
            this.state.valores_empleados = await empleadosUnicos;

            }
            await this.construirGraficaDocumentos(this.state.ordenes, this.state.ordenes_asignar, this.state.ordenes_procesadas, this.state.ordenes_procesar);
            await this.construirGraficaEmpleados('chartdiv', await this.state.valores_empleados);
        }

    }

    formatTimeFloat(floatNumber) {
            const hours = Math.floor(floatNumber); // Parte entera (horas)
            const minutes = Math.round((floatNumber - hours) * 60); // Parte decimal convertida a minutos

            // Aseguramos que los minutos siempre tengan dos dígitos
            const formattedMinutes = minutes.toString().padStart(2, '0');

            return `${hours}:${formattedMinutes}`;
        }

    async filtrar(id) {
    // Evita múltiples ejecuciones simultáneas
    if (this.isFiltering) {
        console.warn("Filtrar ya está en proceso. Ignorando llamada.");
        return;
    }
    this.isFiltering = true; // Marca como en proceso

    try {
        if (this.state.fecha_inicio && this.state.fecha_fin){
        const numberFormatter = new Intl.NumberFormat('es-ES', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });

        let empleados;
        if (id[0] !== 'todos') {
            empleados = await this.orm.search('sale.montacargas', [['activo', '=', true], ['id', 'in', id],['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
        } else {
            empleados = await this.orm.search('sale.montacargas', [['activo', '=', true],['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
        }

        const datos_empleados = await this.orm.read('sale.montacargas', empleados, ['image_1920', 'user_id', 'id', 'funcion']);
        var fechaInicio = this.state.fecha_inicio;
        var fechaFin = this.state.fecha_fin;
        const valoresCalculados = await Promise.all(
            datos_empleados.map(async (empleado) => {
                const valores =  await this.calcular_documentos(empleado.id, fechaInicio, fechaFin);
                const documentos = await valores[7];
                const productos = await valores[8];
                const valor = numberFormatter.format(await valores[9]);
                const valor_real = await valores[9];
                const cumplimiento = await valores[0];
                const procesado = await valores[1];
                const en_proceso = await valores[2];
                const productos_procesado = await valores[3];
                const productos_en_proceso = await valores[4];
                const valor_procesado = numberFormatter.format(await valores[5]);
                const valor_procesado_real = await valores[5];
                const valor_en_proceso = numberFormatter.format(await valores[6]);
                const cumplimiento_productos = numberFormatter.format(await valores[9]);
                const hora_inicio = numberFormatter.format(await valores[10]);
                const hora_fin = numberFormatter.format(await valores[11]);
                const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                const errores_sobrante = await valores[13];
                const errores_faltante = await valores[14];
                const errores_trocado = await valores[15];
                return { ...empleado, documentos, productos,valor,tiempo_promedio,
                    errores_sobrante,
                    errores_faltante,
                    errores_trocado, valor_real, cumplimiento, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
            })
        );

        const empleadosUnicos = Object.values(
            valoresCalculados.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );
        this.state.valores_empleados = await empleadosUnicos;
        }
        else{
            const numberFormatter = new Intl.NumberFormat('es-ES', {
                style: 'decimal',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            });


            let empleados;
            if (id[0] !== 'todos') {
                empleados = await this.orm.search('sale.montacargas', [['activo', '=', true], ['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']], ['id', 'in', id]]);
            } else {
                empleados = await this.orm.search('sale.montacargas', [['activo', '=', true], ['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
            }

            const datos_empleados = await this.orm.read('sale.montacargas', empleados, ['image_1920', 'user_id', 'id', 'funcion']);

            const valoresCalculados = await Promise.all(
                datos_empleados.map(async (empleado) => {
                    const valores =  await this.calcular_documentos(empleado.id);
                    const documentos = await valores[7];
                    const productos = await valores[8];
                    const valor = numberFormatter.format(await valores[9]);
                    const cumplimiento = await valores[0];
                    const procesado = await valores[1];
                    const en_proceso = await valores[2];
                    const productos_procesado = await valores[3];
                    const productos_en_proceso = await valores[4];
                    const valor_procesado = numberFormatter.format(await valores[5]);
                    const valor_procesado_real = await valores[5];
                    const valor_en_proceso = numberFormatter.format(await valores[6]);
                    const cumplimiento_productos = numberFormatter.format(await valores[9]);
                    const hora_inicio = numberFormatter.format(await valores[10]);
                    const hora_fin = numberFormatter.format(await valores[11]);
                    const tiempo_promedio = this.formatTimeFloat(await valores[12]);
                    const errores_sobrante = await valores[13];
                    const errores_faltante = await valores[14];
                    const errores_trocado = await valores[15];
                    return { ...empleado, documentos, productos,valor,tiempo_promedio,
                        errores_sobrante,
                        errores_faltante,
                        errores_trocado, valor_real, cumplimiento, procesado, en_proceso, productos_procesado, productos_en_proceso, valor_procesado, valor_en_proceso, valor_procesado_real,  hora_inicio, hora_fin}; // Agrega el valor al empleado
                })
            );

            const empleadosUnicos = Object.values(
                valoresCalculados.reduce((acc, empleado) => {
                        const nombre = empleado.user_id[0];

                        if (!acc[nombre]) {
                            // Si el empleado no está en el acumulador, lo agrega.
                            acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                        } else {
                            // Si ya existe, concatena las funciones.
                            acc[nombre].funcion += `, ${empleado.funcion}`;
                        }

                        return acc;
                    }, {})
            );
            this.state.valores_empleados = await empleadosUnicos;
    }
    }
    catch (error) {
        console.error("Error al filtrar empleados:", error);
    } finally {
        this.isFiltering = false; // Marca como completado
    }

    await this.construirGraficaDocumentos(this.state.ordenes, this.state.ordenes_asignar, this.state.ordenes_procesadas, this.state.ordenes_procesar);
    await this.construirGraficaEmpleados('chartdiv', await this.state.valores_empleados);
}

    async calcular_datos(id = false){
        const numberFormatter = new Intl.NumberFormat('es-ES', {
            style: 'decimal',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });

        var empleados = await this.orm.search('sale.montacargas', [['activo', '=', true],['funcion','not in', ['piso01','piso02','piso03','piso04','piso05']]]);
        const datos_empleados_selection = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);
        const empleadosSelection = Object.values(
            datos_empleados_selection.reduce((acc, empleado) => {
                    const nombre = empleado.user_id[0];

                    if (!acc[nombre]) {
                        // Si el empleado no está en el acumulador, lo agrega.
                        acc[nombre] = { ...empleado, funcion: empleado.funcion || "" };
                    } else {
                        // Si ya existe, concatena las funciones.
                        acc[nombre].funcion += `, ${empleado.funcion}`;
                    }

                    return acc;
                }, {})
        );
        this.state.valores_empleados_selection = empleadosSelection;
        const datos_empleados = await this.orm.read('sale.montacargas', empleados ,['image_1920', 'user_id', 'id','funcion',]);

        const today = luxon.DateTime.now();
        let fechaInicio, fechaFin;
        fechaInicio = today.startOf("day").toISODate();
        fechaFin = today.endOf("day").toISODate();
        
        var ordenes = await this.orm.search('sale.order', [['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        const productos_ordenes = await this.orm.call("sale.order", "contar_productos", [ordenes]);
        const sumar_ordenes = await this.orm.call("sale.order", "sumar_ordenes", [ordenes]);
        this.state.sumar_ordenes = sumar_ordenes;
        this.state.ordenes = ordenes.length;
        this.state.productos_ordenes= productos_ordenes;

        var asignadas = await this.orm.search('sale.order', [['delivery_status','!=','full'],['procesada','=',false],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_asignar = asignadas.length;
        const productos_ordenes_asignar = await this.orm.call("sale.order", "contar_productos", [asignadas]);
        const sumar_ordenes_asignadas = await this.orm.call("sale.order", "sumar_ordenes", [asignadas]);
        this.state.sumar_ordenes_asignadas = sumar_ordenes_asignadas;
        this.state.productos_ordenes_asignar = productos_ordenes_asignar;

        var procesadas = await this.orm.search('sale.order', [['delivery_status','=','full'],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_procesadas = procesadas.length;
        const productos_ordenes_procesadas = await this.orm.call("sale.order", "contar_productos", [procesadas]);
        const sumar_ordenes_procesadas = await this.orm.call("sale.order", "sumar_ordenes", [procesadas]);
        this.state.sumar_ordenes_procesadas = sumar_ordenes_procesadas;
        this.state.productos_ordenes_procesadas = productos_ordenes_procesadas;

        var procesar = await this.orm.search('sale.order', [['delivery_status','!=','full'],['delivery_status','!=','full'],['procesada','=',true],['state', 'not in', ['draft', 'sent', 'cancel']],['date_order','<=',fechaFin],['date_order','>=',fechaInicio]]);
        this.state.ordenes_procesar = procesar.length;
        const productos_ordenes_procesar = await this.orm.call("sale.order", "contar_productos", [procesar]);
        const sumar_ordenes_procesar = await this.orm.call("sale.order", "sumar_ordenes", [procesar]);
        this.state.sumar_ordenes_procesar = sumar_ordenes_procesar;
        this.state.productos_ordenes_procesar = productos_ordenes_procesar;

        this.state.cumplimiento = Math.round((this.state.ordenes_procesadas/this.state.ordenes)*100);
        this.state.cumplimiento_productos = Math.round((this.state.productos_ordenes_procesadas/this.state.productos_ordenes)*100);
        this.state.cumplimiento_valor = Math.round((this.state.sumar_ordenes_procesadas/this.state.sumar_ordenes)*100);
        this.state.cumplimiento_porcentajes = Math.round((this.state.cumplimiento+this.state.cumplimiento_productos+this.state.cumplimiento_valor)/3);

        // Formatear los valores antes de asignarlos al estado
        this.state.sumar_ordenes = numberFormatter.format(sumar_ordenes);
        this.state.sumar_ordenes_asignadas = numberFormatter.format(sumar_ordenes_asignadas);
        this.state.sumar_ordenes_procesadas = numberFormatter.format(sumar_ordenes_procesadas);
        this.state.sumar_ordenes_procesar = numberFormatter.format(sumar_ordenes_procesar);

    }

    async calcular_documentos(empleado, fechaInicio = false, fechaFin = false) {
        const num_ordenes = await this.orm.call("stock.picking", "calcular_cumplimiento", [[], [empleado, fechaInicio, fechaFin]]);
        return num_ordenes // Actualiza el estado del componente
    }

    async construirGraficaEmpleados(chartId, empleados) {
        am5.ready(function() {
        // Create root element
        am5.array.each(am5.registry.rootElements,
           function(root) {
              try{
                  if (root.dom.id == chartId) {
                     root.dispose();
                     return;
                  }
              }
              catch(error){}
           }
        );

        var root = am5.Root.new(chartId);

        // Set themes
        root.setThemes([
            am5themes_Animated.new(root)
        ]);

        const data = empleados.map(empleado => {

            const category = typeof empleado.user_id?.[1] === "string"
                ? empleado.user_id[1].split(" ").slice(0, 2).join(" ")
                : "Sin nombre";


            const cumplimiento_docs = empleado.cumplimiento || 0;

            const cumplimiento_productos =
                empleado.productos > 0
                    ? Math.round(
                        (empleado.productos_procesado / empleado.productos) * 100
                      )
                    : 0;

            const cumplimiento_valor =
                empleado.valor_real > 0
                    ? Math.round(
                        (empleado.valor_procesado_real / empleado.valor_real) * 100
                      )
                    : 0;


            var cumplimiento_promedio = Math.round(
                (
                    cumplimiento_docs +
                    cumplimiento_productos +
                    cumplimiento_valor
                ) / 3
            );

            if(empleado.funcion.includes('montacargas')){
                cumplimiento_promedio = Math.round( cumplimiento_productos );
            };

            return {
                category: category,
                value: cumplimiento_promedio
            };

        });

        root.setThemes([
        am5themes_Animated.new(root)
            ]);


            // Create chart
            // https://www.amcharts.com/docs/v5/charts/xy-chart/
            let chart = root.container.children.push(am5xy.XYChart.new(root, {
              panX: true,
              panY: true,
              pinchZoomX: true,
              paddingLeft: 0
            }));


            // Add cursor
            // https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/
            let cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
            cursor.lineY.set("visible", false);


            // Create axes
            // https://www.amcharts.com/docs/v5/charts/xy-chart/axes/
            let xRenderer = am5xy.AxisRendererX.new(root, {
              minGridDistance: 15,
              minorGridEnabled: true
            });

            xRenderer.labels.template.setAll({
              rotation: -90,
              centerY: am5.p50,
              centerX: 0,
              fontSize: "10px"
            });

            xRenderer.grid.template.setAll({
              visible: false
            });

            let xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
              maxDeviation: 0.3,
              categoryField: "category",
              renderer: xRenderer,
              tooltip: am5.Tooltip.new(root, {})
            }));

            let yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
              maxDeviation: 0.3,
              min: 0,
              max: 100,
              strictMinMax: true,
              renderer: am5xy.AxisRendererY.new(root, {})
              }));


            // Create series
            // https://www.amcharts.com/docs/v5/charts/xy-chart/series/
            let series = chart.series.push(am5xy.ColumnSeries.new(root, {
              xAxis: xAxis,
              yAxis: yAxis,
              valueYField: "value",
              categoryXField: "category",
              adjustBulletPosition: false,
              tooltip: am5.Tooltip.new(root, {
                labelText: "{valueY}"
              })
            }));

            series.columns.template.setAll({
              width: 4
            });

            series.columns.template.adapters.add("fill", function (fill, target) {
                const value = target.dataItem.get("valueY");
                if (value < 50) {
                    return am5.color(0xff0000); // Rojo
                } else if (value === 100) {
                    return am5.color(0x00ff00); // Verde
                } else {
                    return am5.color(0xffff00); // Amarillo
                }
            });

            series.columns.template.adapters.add("stroke", function (stroke, target) {
                const value = target.dataItem.get("valueY");
                if (value < 50) {
                    return am5.color(0xff0000); // Rojo
                } else if (value === 100) {
                    return am5.color(0x00ff00); // Verde
                } else {
                    return am5.color(0xfff000); // Amarillo
                }
            });

            series.bullets.push(function() {
              return am5.Bullet.new(root, {
                locationY: 1,
                sprite: am5.Circle.new(root, {
                  radius: 5
                })
              })
            })

            xAxis.data.setAll(data);
            series.data.setAll(data);


            // Make stuff animate on load
            // https://www.amcharts.com/docs/v5/concepts/animations/
            series.appear(1000);
            chart.appear(1000, 100);
    });
    }

    async construirGraficaDocumentos(ordenes, ordenes_asignar, ordenes_procesadas, ordenes_procesar) {
        am5.ready(function() {
        // Create root element
        am5.array.each(am5.registry.rootElements,
           function(root) {
           try{
              if (root.dom.id == 'chartdiv2') {
                 root.dispose();
              }
             }
             catch(error){}
           }
        );

        var root = am5.Root.new('chartdiv2');

        // Set themes
        root.setThemes([
            am5themes_Animated.new(root)
        ]);

        var data = [
            {
                category: "Ordenes",
                value: ordenes
            },
            {
                category: "Por Asignar",
                value: ordenes_asignar
            },
            {
                category: "Por Procesar",
                value: ordenes_procesar
            },
            {
                category: "Procesadas",
                value: ordenes_procesadas
            }
        ];

        root.setThemes([
        am5themes_Animated.new(root)
            ]);


            // Create chart
            // https://www.amcharts.com/docs/v5/charts/xy-chart/
            let chart = root.container.children.push(am5xy.XYChart.new(root, {
              panX: true,
              panY: true,
              pinchZoomX: true,
              paddingLeft: 0
            }));


            // Add cursor
            // https://www.amcharts.com/docs/v5/charts/xy-chart/cursor/
            let cursor = chart.set("cursor", am5xy.XYCursor.new(root, {}));
            cursor.lineY.set("visible", false);


            // Create axes
            // https://www.amcharts.com/docs/v5/charts/xy-chart/axes/
            let xRenderer = am5xy.AxisRendererX.new(root, {
              minGridDistance: 15,
              minorGridEnabled: true
            });

            xRenderer.labels.template.setAll({
              centerY: am5.p50,
              centerX: am5.p50,
              fontSize: "15px"
            });

            xRenderer.grid.template.setAll({
              visible: false
            });

            let xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
              maxDeviation: 0.3,
              categoryField: "category",
              renderer: xRenderer,
              min: 0,
              tooltip: am5.Tooltip.new(root, {})
            }));

            let yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
              maxDeviation: 0.3,
              strictMinMax: true,
              min: 0,
              renderer: am5xy.AxisRendererY.new(root, {})
              }));


            // Create series
            // https://www.amcharts.com/docs/v5/charts/xy-chart/series/
            let series = chart.series.push(am5xy.ColumnSeries.new(root, {
              xAxis: xAxis,
              yAxis: yAxis,
              valueYField: "value",
              categoryXField: "category",
              adjustBulletPosition: false,
              tooltip: am5.Tooltip.new(root, {
                labelText: "{valueY}"
              })
            }));

            series.columns.template.setAll({
              width: 50
            });

            series.columns.template.adapters.add("fill", function (fill, target) {
                const value = target.dataItem.get("valueY");
                if (value < (ordenes/2)) {
                    return am5.color(0xff0000); // Rojo
                } else if (value === ordenes) {
                    return am5.color(0x00ff00); // Verde
                } else {
                    return am5.color(0xffff00); // Amarillo
                }
            });

            series.columns.template.adapters.add("stroke", function (stroke, target) {
                const value = target.dataItem.get("valueY");
                if (value < (ordenes/2)) {
                    return am5.color(0xff0000); // Rojo
                } else if (value === ordenes) {
                    return am5.color(0x00ff00); // Verde
                } else {
                    return am5.color(0xfff000); // Amarillo
                }
            });

            series.bullets.push(function() {
              return am5.Bullet.new(root, {
                locationY: 1,
                sprite: am5.Circle.new(root, {
                  radius: 5
                })
              })
            })

            xAxis.data.setAll(data);
            series.data.setAll(data);


            // Make stuff animate on load
            // https://www.amcharts.com/docs/v5/concepts/animations/
            series.appear(1000);
            chart.appear(1000, 100);
    });
    }
}

OwlInformDashboard.template = "productivity_dashboard_template"
registry.category("actions").add("productivity_dashboard_template", OwlInformDashboard)

