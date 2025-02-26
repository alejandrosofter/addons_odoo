/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";
class SystrayIcon extends Component {
  setup() {
    super.setup(...arguments);
    this.action = useService("action");
    this.rpc = useService("rpc");
    this.state = useState({ status: "offline", activeWsap: false });
    onMounted(async () => {
      this.fetchBotStatus();
    });
  }
  async fetchBotStatus() {
    try {
      const result = await this.rpc("/systray/wsap/get_status");

      let color = result.status_session === "open" ? "#00ff2d" : "#ff7070";

      if (result.activeWsap === false) {
        color = "#ffac00";
      }
      this.state = { ...result, color };
      this.render();
    } catch (error) {
      console.error("Error al obtener el estado del bot:", error);
    }
  }
  async _onClick() {
    this.action.doAction({
      type: "ir.actions.act_window",
      res_model: "bot.whatsapp",
      view_mode: "tree",
      views: [
        [false, "tree"],
        [false, "form"],
      ], // Primero tree, luego form
      target: "current", // Abre en la misma vista de Odoo
    });
  }
}
SystrayIcon.template = "systray_icon_wsap";
export const systrayItem = {
  Component: SystrayIcon,
};
registry.category("systray").add("SystrayIcon", systrayItem, { sequence: 1 });
