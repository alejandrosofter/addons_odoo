from odoo import fields, models, api
from odoo.exceptions import UserError
import requests
import time
import pytz
from datetime import datetime

# Intentar importar los componentes de LangChain. Si no están instalados,
# las funcionalidades de IA no estarán disponibles, pero el módulo no fallará.
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None
try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.tools import tool
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    AgentExecutor = None
    create_tool_calling_agent = None
    tool = None
    ChatPromptTemplate = None


class IaQuery(models.Model):
    """
    Modelo para registrar consultas de IA.
    """

    _name = "ia.query"
    _description = "Consulta de IA"

    fecha = fields.Datetime(
        "Fecha",
        default=fields.Datetime.now,
        required=True,
    )
    query = fields.Text("Consulta", required=True)
    result = fields.Text("Resultado")
    agent_id = fields.Many2one(
        "ia.agente",
        string="Agente IA",
        required=True,
    )
    time = fields.Float("Tiempo de Procesamiento (segundos)")
    procesado = fields.Boolean("Procesado", default=False)
    partner_id = fields.Many2one("res.partner", string="Partner")

    def _get_partner_context(self):
        """
        Genera un string con la información relevante del partner
        para el contexto de IA.
        """
        self.ensure_one()
        if not self.partner_id:
            return ""

        partner = self.partner_id
        context_parts = []
        context_parts.append(f"Nombre: {partner.name or ''}")
        if partner.email:
            context_parts.append(f"Email: {partner.email}")
        if partner.mobile:
            context_parts.append(f"Móvil: {partner.mobile}")
        if partner.vat:
            context_parts.append(f"VAT: {partner.vat}")
        if (
            hasattr(partner, "l10n_ar_afip_responsibility_type_id")
            and partner.l10n_ar_afip_responsibility_type_id
        ):
            context_parts.append(
                "Responsabilidad AFIP: "
                f"{partner.l10n_ar_afip_responsibility_type_id.name}"
            )
        address_parts = [
            partner.street or "",
            partner.street2 or "",
            partner.city or "",
            partner.zip or "",
            partner.state_id.name or "",
            partner.country_id.name or "",
        ]
        full_address = ", ".join(filter(None, address_parts))
        if full_address:
            context_parts.append(f"Domicilio: {full_address}")

        return "Datos del Partner:\n" + "\n".join(context_parts)

    def _get_user_context(self):
        """
        Genera un string con la información relevante del usuario
        para el contexto de IA.
        Prioriza el usuario asociado al partner de la consulta,
        si no, usa el usuario actual.
        """
        self.ensure_one()
        user = None
        if self.partner_id:
            user = self.env["res.users"].search(
                [("partner_id", "=", self.partner_id.id)], limit=1
            )

        if not user:
            return "No tiene usuario"

        context_parts = []
        context_parts.append(f"Nombre de Usuario: {user.name or ''}")
        if user.login:
            context_parts.append(f"Login: {user.login}")
        if user.email:
            context_parts.append(f"Email de Usuario: {user.email}")
        if user.partner_id:
            context_parts.append("Partner Asociado: " + (user.partner_id.name or ""))

        return "Datos del Usuario:\n" + "\n".join(context_parts)

    def _get_current_datetime_str(self):
        """
        Obtiene la fecha y hora actual en la zona horaria de Argentina
        y la formatea como una cadena de texto.
        """
        self.ensure_one()
        argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")
        current_datetime = datetime.now(argentina_tz)
        current_datetime_str = current_datetime.strftime("%Y-%m-%d %H:%M:%S %Z%z")

        agent_query = (
            f"Fecha y Hora Actual: {current_datetime_str}\n\n"
            + f"Consulta: {self.query}"
        )
        return agent_query

    def _create_agent(self, llm, tools):
        """
        Crea y configura un agente de LangChain con el LLM y las herramientas dadas.
        """
        self.ensure_one()
        if not (AgentExecutor and create_tool_calling_agent and ChatPromptTemplate):
            raise UserError("Componentes de LangChain para Agente no están instalados.")

        # The agent's system message comes from self.agent_id.prompt
        system_message = self.agent_id.prompt
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Create the agent
        agent = create_tool_calling_agent(llm, tools, prompt_template)

        # Create the agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
        )
        return agent_executor

    def _get_tools(self):
        """
        Define y retorna las herramientas disponibles para el agente de IA.
        """
        self.ensure_one()
        env = self.env  # Capturar el entorno para usarlo en las tools

        @tool
        def get_current_odoo_status(query: str) -> str:
            """
            Útil para obtener información general del entorno Odoo
            o para responder preguntas relacionadas con Odoo.
            """
            return "El sistema Odoo está operativo y listo para " "responder consultas."

        @tool
        def buscar_contactos(query: str) -> str:
            """
            Busca contactos por nombre en Odoo.
            Retorna una lista de contactos con su nombre y email (si disponible).
            """
            print(f"query {query}")
            partners = env["res.partner"].search([("name", "ilike", query)], limit=5)
            if not partners:
                return "No se encontraron contactos."

            results = []
            for partner in partners:
                contact_info = f"Nombre: {partner.name}"
                if partner.email:
                    contact_info += f", Email: {partner.email}"
                results.append(contact_info)
            return "Contactos encontrados:\n" + "\n".join(results)

        tools = [get_current_odoo_status, buscar_contactos]
        return tools

    # From then on you can log into your server via SSH2 as user "root" with the following password: VJKHt8Wa8zHsXY

    def _get_llm(self):
        """
        Inicializa y retorna el objeto LLM (Large Language Model)
        basado en la configuración del agente.
        """
        self.ensure_one()
        config = self.agent_id._get_langchain_settings()
        model_name_param = self.agent_id.model_name
        provider = self.agent_id.get_provider_from_model_name(model_name_param)
        llm = None

        if provider == "openai":
            if not ChatOpenAI:
                raise UserError("El paquete 'langchain-openai' no está " "instalado.")
            llm = ChatOpenAI(**config)
        elif provider == "gemini":
            if not ChatGoogleGenerativeAI:
                raise UserError(
                    "El paquete 'langchain-google-genai' no está " "instalado."
                )
            llm = ChatGoogleGenerativeAI(**config)
        elif provider == "deepseek":
            if not ChatOpenAI:
                raise UserError(
                    "El paquete 'langchain-openai' no está "
                    "instalado (para DeepSeek)."
                )
            llm = ChatOpenAI(**config)
        else:
            raise UserError(
                "Error: Modelo IA no soportado. "
                f"(Modelo: {self.agent_id.model_name})"
            )
        return llm

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        # Procesar automáticamente solo si 'procesado' no está en vals_list
        # o si no se está creando un registro ya procesado.
        for record in records:
            if "procesado" not in vals_list or not vals_list["procesado"]:
                record._process_query_with_llm()
        return records

    def action_process_query(self):
        self.ensure_one()
        # if self.procesado:
        #     raise UserError("Esta consulta ya ha sido procesada.")
        self._process_query_with_llm()

    def _process_query_with_llm(self):
        self.ensure_one()
        self.time = 0.0
        self.procesado = False
        if not self.agent_id:
            self.result = "Error: No hay agente IA asociado a esta consulta."
            return

        llm = None
        agent_query = self._get_current_datetime_str()
        partner_context = self._get_partner_context()
        user_context = self._get_user_context()
        agent_query = f"{user_context}\n\n{partner_context}\n\n{agent_query}"

        start_time = time.time()
        try:
            llm = self._get_llm()

            tools = self._get_tools()

            agent_executor = self._create_agent(llm, tools)

            # Run the agent
            response = agent_executor.invoke({"input": agent_query})
            self.result = response["output"]
            self.procesado = True

        except requests.exceptions.RequestException as e:
            self.result = f"Error de conexión con la API de IA: {e}"
        except UserError as e:
            self.result = f"Error de configuración: {e}"
        except Exception as e:
            self.result = f"Error inesperado al procesar la consulta: {e}"
        finally:
            end_time = time.time()
            self.time = end_time - start_time
