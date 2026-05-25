import type { IFormattedData } from "@/assets/interfaces/IForm";
import ParamsHeaderIcons from "@/views/configurator/components/ParamsHeaderIcons.vue";
import {h} from 'vue';

export const createLabelIconsComponent = (param: IFormattedData, onDescriptionClicked: ()=> void) => {
            return h(ParamsHeaderIcons,
                {
                    needReq: true,
                    needDescription: Boolean('description' in param && param.description),
                    onDescriptionClicked,
                })
        }