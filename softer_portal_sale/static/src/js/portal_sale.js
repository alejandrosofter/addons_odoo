odoo.define("softer_portal_sale.portal_sale", [], function (require) {
  "use strict";

  // Prueba de carga del JavaScript
  console.log("JavaScript cargado correctamente!");

  $(document).ready(function () {
    // Seleccionar todas las órdenes
    $("#select_all_orders").on("change", function () {
      var checked = $(this).prop("checked");
      $(".order-checkbox").prop("checked", checked);
      updateGenerateButton();
    });

    // Cambio en checkbox individual
    $(".order-checkbox").on("change", function () {
      var allChecked =
        $(".order-checkbox:checked").length === $(".order-checkbox").length;
      $("#select_all_orders").prop("checked", allChecked);
      updateGenerateButton();
    });

    // Actualizar estado del botón
    function updateGenerateButton() {
      var hasSelectedOrders = $(".order-checkbox:checked").length > 0;
      $("#generate_invoice_button").prop("disabled", !hasSelectedOrders);
    }

    // Generar factura
    $("#generate_invoice_button").on("click", function () {
      var $button = $(this);
      var orderIds = $(".order-checkbox:checked")
        .map(function () {
          return $(this).val();
        })
        .get();

      if (orderIds.length === 0) {
        alert("Por favor seleccione al menos una orden");
        return;
      }

      // Deshabilitar el botón y mostrar loader
      $button.prop("disabled", true);
      $button.html('<i class="fa fa-spinner fa-spin"></i> Procesando...');

      // Obtener el token CSRF
      var token = $('meta[name="csrf-token"]').attr("content");
      if (!token) {
        token = odoo.csrf_token;
      }
      if (!token) {
        alert("Error: No se pudo obtener el token de seguridad");
        restoreButton($button);
        return;
      }

      console.log("Token CSRF:", token);
      console.log("Order IDs:", orderIds);

      $.ajax({
        url: "/my/orders/generate_invoice",
        type: "POST",
        data: {
          order_ids: orderIds.join(","),
          csrf_token: token,
        },
        success: function (response) {
          try {
            var data =
              typeof response === "string" ? JSON.parse(response) : response;
            if (data.success && data.redirect_url) {
              window.location.href = data.redirect_url;
            } else if (data.error) {
              alert(data.error);
              restoreButton($button);
            } else {
              alert("Error inesperado al generar la factura");
              restoreButton($button);
            }
          } catch (e) {
            console.error("Error al procesar la respuesta:", e);
            alert("Error al procesar la respuesta del servidor");
            restoreButton($button);
          }
        },
        error: function (xhr, status, error) {
          console.error("Error:", error);
          console.error("Status:", status);
          console.error("Response:", xhr.responseText);
          alert("Error al generar la factura: " + error);
          restoreButton($button);
        },
      });
    });

    // Función para restaurar el estado del botón
    function restoreButton($button) {
      $button.prop("disabled", false);
      $button.html(
        '<i class="fa fa-file-invoice"></i><span>Generar Factura</span>'
      );
    }
  });
});
