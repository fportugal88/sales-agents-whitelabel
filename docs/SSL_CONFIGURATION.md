# Configuração SSL para Ambientes Corporativos

Este documento explica como configurar SSL quando você está em um ambiente corporativo com proxy/firewall que usa certificados auto-assinados.

## Problema

Em ambientes corporativos, você pode encontrar o seguinte erro:

```
httpcore.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain
```

Isso acontece porque o proxy/firewall corporativo intercepta conexões HTTPS usando certificados auto-assinados que não são reconhecidos pelo Python.

## Solução 1: Truststore (Recomendada)

A solução mais segura e recomendada é usar o `truststore`, que injeta certificados do sistema operacional no SSL do Python.

### Instalação

```bash
pip install truststore
```

### Como Funciona

O `truststore` injeta automaticamente os certificados confiáveis do sistema operacional (Windows Certificate Store, macOS Keychain, Linux ca-certificates) no SSL do Python. Isso permite que o Python reconheça certificados corporativos que já estão instalados no sistema.

### Uso

Não é necessária nenhuma configuração adicional! O sistema detecta automaticamente se o `truststore` está instalado e o usa.

O código já está configurado para injetar truststore no início do servidor (em `src/api/server.py`).

### Verificação

Se o truststore estiver funcionando, você verá no log:

```
INFO: Truststore injetado - usando certificados do sistema
```

Se não estiver instalado, você verá:

```
INFO: Truststore não instalado - usando certificados padrão do Python
```

## Solução 2: Desabilitar Verificação SSL (Apenas Desenvolvimento)

⚠️ **ATENÇÃO**: Use apenas em desenvolvimento local, **NUNCA em produção**!

Se o truststore não resolver o problema, você pode temporariamente desabilitar a verificação SSL:

### Configuração

Adicione no arquivo `.env`:

```env
SSL_VERIFY=false
```

### Avisos

- Isso desabilita completamente a verificação de certificados SSL
- Sua aplicação ficará vulnerável a ataques man-in-the-middle
- Use apenas para desenvolvimento e testes locais
- **Nunca use em produção ou com dados sensíveis**

## Recomendações

1. **Sempre tente a Solução 1 primeiro** (truststore)
2. Se truststore não funcionar, verifique se os certificados corporativos estão instalados no sistema
3. Use `SSL_VERIFY=false` apenas como último recurso em desenvolvimento
4. Em produção, sempre use certificados válidos e truststore

## Troubleshooting

### Truststore não funciona

1. Verifique se está instalado: `pip list | grep truststore`
2. Verifique se os certificados corporativos estão no sistema
3. No Windows: Verifique "Autoridades de Certificação Raiz Confiáveis" no Gerenciador de Certificados
4. No Linux: Verifique `/etc/ssl/certs/` ou `/usr/local/share/ca-certificates/`

### Erro persiste mesmo com truststore

1. Verifique se o certificado corporativo está instalado no sistema
2. Tente adicionar manualmente o certificado ao repositório do sistema
3. Como último recurso em desenvolvimento, use `SSL_VERIFY=false`

## Referências

- [Truststore Documentation](https://github.com/sethmlarson/truststore)
- [Strands Agents Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/quickstart/python/)

