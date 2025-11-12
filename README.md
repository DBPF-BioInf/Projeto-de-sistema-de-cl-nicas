🏥 Sistema de clínicas

Este algoritmo um sistema web desenvolvido em Flask que permite gerenciar usuários, clínicas, pacientes e créditos, com autenticação segura e níveis de acesso diferenciados (profissional e administrador).

Este projeto foi pensado para ambientes clínicos, onde múltiplos profissionais trabalham sob uma mesma clínica e precisam registrar e acompanhar pacientes — tudo de forma organizada e protegida.

🚀 Funcionalidades Principais
👩‍⚕️ Usuários

Registro e login de profissionais com senha criptografada.

Associação de usuários a uma clínica específica.

Controle de créditos individuais (úteis para limitar o uso de ferramentas ou análises).

🧒 Pacientes

Cadastro, edição e exclusão de pacientes vinculados a clínicas.

Associação de pacientes a um ou mais profissionais responsáveis.

Acesso restrito: o profissional só visualiza pacientes sob seus cuidados.

🏢 Clínicas

Registro de clínicas e vinculação de usuários e pacientes a elas.

Controle administrativo centralizado.

🧠 Área Administrativa

Painel exclusivo para o administrador:

Gerenciar usuários e créditos.

Cadastrar e editar clínicas.

Atribuir profissionais a clínicas.

Adicionar, editar e excluir pacientes.
