// public/app_v2.js - Frontend conectado a Python en Render

// ⚠️ REEMPLAZAR: Coloca aquí tu Public Key de Producción (LIVE)
// Ejemplo: "APP_USR-12345678-1234-1234-1234-1234567890ab"
const mp = new MercadoPago("[TU_PUBLIC_KEY_DE_PRODUCCION_AQUI]", {
  locale: "es-PE",
});

function createCardForm() {
  const installmentsGroup = document.getElementById("installments-group");

  try {
    const cardForm = mp.cardForm({
      amount: "1.00",
      iframe: true,
      form: {
        id: "form-checkout",
        cardholderEmail: { id: "form-checkout__cardholderEmail" },
        cardholderName: { id: "form-checkout__cardholderName" },
        expirationDate: { id: "form-checkout__expirationDate" },
        securityCode: { id: "form-checkout__securityCode" },
        cardNumber: { id: "form-checkout__cardNumber" },
        installments: { id: "form-checkout__installments" },
        issuer: { id: "form-checkout__issuer" },
        paymentMethod: { id: "form-checkout__paymentMethod" },
      },
      callbacks: {
        onFormMounted: (error) => {
          if (error) return console.warn("Error montaje:", error);
          console.log("Formulario montado.");
        },
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
          const finalInstallments =
            installmentsGroup.style.display === "none"
              ? 1
              : Number(installments);

          try {
            // 🚀 URL DE RENDER (PRODUCCIÓN)
            const response = await fetch(
              "https://livescardapp.onrender.com/procesar-pago",
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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

            // Actualizar listas después del pago
            actualizarListas();

            // Opcional: limpiar formulario
            // document.getElementById("form-checkout").reset();
          } catch (error) {
            console.error("Error:", error);
            alert("Error de comunicación con el servidor.");
          }
        },
      },
    });
    cardForm.mount("card-form-container");
  } catch (e) {
    if (!e.message.includes("CardForm already mounted"))
      console.error("Error crítico:", e);
  }
}

async function actualizarListas() {
  try {
    // 🚀 URL DE RENDER (PRODUCCIÓN)
    const response = await fetch(
      "https://livescardapp.onrender.com/obtener-estados"
    );
    if (!response.ok) throw new Error("Error al obtener estados");

    const data = await response.json();
    const liveList = document.getElementById("live-list");
    const deadList = document.getElementById("dead-list");

    liveList.innerHTML = "";
    deadList.innerHTML = "";

    if (data.live) {
      data.live.forEach((card) => {
        const item = document.createElement("div");
        item.className = "card-item";
        item.innerHTML = `<strong>Terminada en ${card.ultimos4}</strong><br><small>Estado: ${card.status} | ID: ${card.id}</small>`;
        liveList.appendChild(item);
      });
    }
    if (data.dead) {
      data.dead.forEach((card) => {
        const item = document.createElement("div");
        item.className = "card-item";
        item.innerHTML = `<strong>Terminada en ${card.ultimos4}</strong><br><small>Estado: ${card.status} | Detalle: ${card.detail}</small>`;
        deadList.appendChild(item);
      });
    }
  } catch (error) {
    console.error("Error listas:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  createCardForm();
  actualizarListas();
});
