
// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import { waitForApp } from "./utils/comfyapp.ts";
import "./scoped-tailwind.css";
import { app } from "./utils/comfyapp";
import "./fonts.css";
import { TOOLBOX_IDS, TOOLBOX_LABELS } from './constants/enums.ts';

const App = React.lazy(() =>
  import("./App.tsx").then(({ default: App }) => ({
    default: App,
  })),
);

function waitForDocumentBody() {
  return new Promise((resolve) => {
    if (document.body) {
      return resolve(document.body);
    }

    document.addEventListener("DOMContentLoaded", () => {
      resolve(document.body);
    });
  });
}

waitForDocumentBody()
  .then(() => waitForApp())
  .then(() => {
    app.extensionManager.registerSidebarTab({
      id: "comfyui-copilot",
      icon: "cc-icon-logo",
      title: "ComfyUI Copilot",
      tooltip: "ComfyUI Copilot",
      type: "custom",
      render: (el: HTMLElement) => {
        const container = document.createElement("div");
        container.id = "comfyui-copilot-plugin";
        container.className = "h-full w-full flex flex-col";
        el.style.height = "100%";
        el.appendChild(container);
        ReactDOM.createRoot(container).render(
          <React.StrictMode>
            <Suspense fallback={<div className="h-full w-full flex items-center justify-center">Loading...</div>}>
              <App />
            </Suspense>
          </React.StrictMode>,
        );
      },
    });
  }).then(() => {
    app.registerExtension({
      name: 'Copilot_Toolbox',
      commands: [
        {
          id: TOOLBOX_IDS.USAGE,
          label: TOOLBOX_LABELS.USAGE,
          icon: 'pi pi-server',
          function: () => {
            // Command logic here
            console.log('-call-->')
          }
        },
        {
          id: TOOLBOX_IDS.PARAMETERS,
          label: TOOLBOX_LABELS.PARAMETERS,
          icon: 'pi pi-book',
          function: () => {
            // Command logic here
            console.log('-call-->')
          }
        },
        {
          id: 'Downstream_Nodes',
          label: 'Downstream Nodes',
          icon: 'pi pi-arrow-circle-right',
          tooltip: '111',
          function: () => {
            // Command logic here
            console.log('-call-->')
          }
        }
      ],
      // Return an array of command IDs to show in the selection toolbox
      // when an item is selected
      getSelectionToolboxCommands: (selectedItem: any) => [TOOLBOX_IDS.USAGE, TOOLBOX_IDS.PARAMETERS, 'Downstream_Nodes']
    })
    console.log('111-->', app.extensionManager.getSidebarTabs());
  })
  // .then(() => {
  //   app.extensionManager.setting.set('Comfy.Sidebar.Location', 'left');
  // })
  ;
