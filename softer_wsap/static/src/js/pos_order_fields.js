odoo.define("softer_wsap.pos_order_fields", function (require) {
  "use strict";

  var { Order } = require("point_of_sale.models");
  var { PaymentScreen } = require("point_of_sale.screens");
  var Registries = require("point_of_sale.Registries");

  const PosOrderPhoneNumber = (Order) =>
    class PosOrderPhoneNumber extends Order {
      constructor(obj, options) {
        super(...arguments);
        this.x_phone_number = this.x_phone_number || "";
      }

      init_from_JSON(json) {
        super.init_from_JSON(json);
        this.x_phone_number = json.x_phone_number || "";
      }

      export_as_JSON() {
        const json = super.export_as_JSON();
        json.x_phone_number = this.x_phone_number;
        return json;
      }

      export_for_printing() {
        const json = super.export_for_printing();
        json.x_phone_number = this.x_phone_number;
        return json;
      }

      set_phone_number(phone_number) {
        this.x_phone_number = phone_number;
      }

      get_phone_number() {
        return this.x_phone_number;
      }
    };
  Registries.Model.extend(Order, PosOrderPhoneNumber);

  const PosPaymentScreen = (PaymentScreen) =>
    class PosPaymentScreen extends PaymentScreen {
      onChangePhoneNumber(event) {
        const phoneNumber = event.target.value;
        this.currentOrder.set_phone_number(phoneNumber);
      }
    };
  Registries.Component.extend(PaymentScreen, PosPaymentScreen);
});
