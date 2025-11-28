// public/app_v2.js
// Lógica de frontend para el Verificador de Tarjetas de Crédito.
// Se comunica con el servidor backend de Python (Render).

// ⚠️ CAMBIO NECESARIO: Reemplazar con tu Public Key de Producción (LIVE)
const mp = new MercadoPago("TEST-2f38ac73-cb30-4ce6-9f4a-2e9109822edd", {
  locale: "es-PE",
});

// Función para crear el formulario de tarjeta de forma segura
function createCardForm() {
  const installmentsGroup = document.getElementById("installments-group");

  try {
    const cardForm = mp.cardForm({
      amount: "1.00",
      iframe: true,

      form: {
        id: "form-checkout",

        // Mapeo de campos <INPUT>
        cardholderEmail: {
          id: "form-checkout__cardholderEmail",
        },
        cardholderName: {
          id: "form-checkout__cardholderName",
        },

        // Mapeo de campos <DIV> (Inyección de Iframe)
        expirationDate: {
          id: "form-checkout__expirationDate",
        },
        securityCode: {
          id: "form-checkout__securityCode",
        },
        cardNumber: {
          id: "form-checkout__cardNumber",
        },

        // Mapeo de campo <SELECT> (Cuotas y Emisor)
        installments: {
          id: "form-checkout__installments",
        },
        issuer: {
          id: "form-checkout__issuer",
        },

        // Mapeo de campos auxiliares
        paymentMethod: {
          id: "form-checkout__paymentMethod",
        },
      },

      callbacks: {
        onFormMounted: (error) => {
          if (error)
            return console.warn(
              "Error al montar el formulario de tarjeta:",
              error
            );
          console.log("Formulario de tarjeta montado correctamente.");
        },

        // LÓGICA: Muestra/Oculta Cuotas según el tipo de tarjeta
        onResults: (results) => {
          if (results.type === "card_type") {
            const isCreditCard = results.values.includes("credit_card");

            if (installmentsGroup) {
              installmentsGroup.style.display = isCreditCard ? "block" : "none";
            }
          }
        },

        onSubmit: async (event) => {
          event.preventDefault();

          const { paymentMethodId, issuerId, token, installments } =
            cardForm.getCardFormData();

          const cardholderEmail = document.getElementById(
            "form-checkout__cardholderEmail"
          ).value;

          // Si las cuotas están ocultas (débito), forzar a 1
          const finalInstallments =
            installmentsGroup.style.display === "none"
              ? 1
              : Number(installments);

          // ⚠️ CAMBIO TEMPORAL: Usar LOCALHOST para el backend de Python (puerto 5000)
          try {
            const response = await fetch(
              "http://localhost:5000/procesar-pago",
              {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  token,
                  payment_method_id: paymentMethodId,
                  issuer_id: issuerId,
                  installments: finalInstallments,
                  transaction_amount: "1.00",
                  cardholderEmail: cardholderEmail,
                }),
              }
            );

            const result = await response.json();

            alert(result.message);
            document.getElementById("form-checkout").reset();
            actualizarListas();
          } catch (error) {
            console.error("Error de red o de servidor:", error);
            alert(
              "Ocurrió un error al comunicarse con el servidor. Inténtalo de nuevo."
            );
          }
        },
        onFetching: (resource) => {
          console.log("Obteniendo recurso:", resource);
        },
      },
    });

    cardForm.mount("card-form-container");
  } catch (e) {
    // Silencia el error de doble montaje sin eliminar la protección.
    if (!e.message.includes("CardForm already mounted")) {
      console.error("Error crítico al montar el formulario:", e);
    }
  }
}

// Función para obtener los datos de las tarjetas y renderizarlos en el HTML
async function actualizarListas() {
  try {
    // ⚠️ CAMBIO TEMPORAL: Usar LOCALHOST para el backend de Python (puerto 5000)
    const response = await fetch("http://localhost:5000/obtener-estados");
    if (!response.ok) {
      throw new Error("No se pudo obtener la lista de estados.");
    }
    const data = await response.json();

    const liveList = document.getElementById("live-list");
    const deadList = document.getElementById("dead-list");

    liveList.innerHTML = "";
    deadList.innerHTML = "";

    if (data.live && data.live.length > 0) {
      data.live.forEach((card) => {
        const item = document.createElement("div");
        item.className = "card-item";
        item.innerHTML = `
					<strong>Terminada en **** **** **** ${card.ultimos4}</strong><br>
					<small>Estado: ${card.status} | ID Pago: ${card.id}</small>
				`;
        liveList.appendChild(item);
      });
    } else {
      liveList.innerHTML = "<p>No hay tarjetas live.</p>";
    }

    if (data.dead && data.dead.length > 0) {
      data.dead.forEach((card) => {
        const item = document.createElement("div");
        item.className = "card-item";
        item.innerHTML = `
					<strong>Terminada en **** **** **** ${card.ultimos4}</strong><br>
					<small>Estado: ${card.status} | Detalle: ${card.detail}</small>
				`;
        deadList.appendChild(item);
      });
    } else {
      deadList.innerHTML = "<p>No hay tarjetas dead.</p>";
    }
  } catch (error) {
    console.error("Error al actualizar las listas:", error);
    const liveList = document.getElementById("live-list");
    const deadList = document.getElementById("dead-list");
    liveList.innerHTML = "<p>Error al cargar los datos.</p>";
    deadList.innerHTML = "";
  }
}

// Inicializa la aplicación cuando el contenido de la página se haya cargado completamente
document.addEventListener("DOMContentLoaded", () => {
  createCardForm();
  actualizarListas(); // Carga las listas existentes al empezar
});
