declare module 'vue-image-zoomer' {
    import type { DefineComponent } from 'vue';

    const VueImageZoomer: DefineComponent<any, any, any>;

    export { VueImageZoomer };
    export default VueImageZoomer;
}

declare module 'vue-image-zoomer/dist/style.css' {
    const content: string;
    export default content;
}
