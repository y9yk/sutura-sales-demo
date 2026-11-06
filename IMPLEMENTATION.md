# Implementation plan

Goal: publish a real sutura demonstration onVercel and update the existing article without creating a duplicate post.
Spec: DESIGN.md and this protocol. User requested execution; work continues inline with bounded delegation.

1. Backend owner: server.py, tests/test_server.py, Dockerfile, compose.yaml, vercel.json, requirements.txt(if needed but no packages), data preparation, cases.json. Pythonstdlib only. RealSuturaCLI runs perrequest; never simulate product output. Serve UI frompublic/. Independently tested protocol boundaries.
2. UI owner(parent): public/index.html, embed.html, app.js, style.css. System black/white editorial UI. APIprotocol below. Realbrowser desktop/mobile QA and visualverdict before edits.
3. Build pinned multiarchcontainer; integrationtest allscenarios againstactualsutura. Create isolatedgitrepository and publicGitHubrepo under authenticatedy9yk after secret/artifact review. Lorecommitformat.
4. Vercel userlogin, configureGitHubimport/Containerpreset, deploy and verifyanonymouspublicAPI and UI. No credential export or globalpermissionchanges. If a feature/plan blocker appears, retain concretebuild and exact error, choose a supportedVercelpath if possible.
5. Rewrite samearticle to integrate actualproducttests/demo/repo instead of a separatePart2. Prepare/read immutableBearblogedit, show exactrevision, execute once againstuserrequest. Verify title/date/URL/images/iframe or link, cite actualmeasurements and limitations.

## API contract
GET /api/catalog → {engine:{name:"sutura",version:"0.11.0",image:"..."},scenarios:[{id,title,question,description,baseline_label,kind}],limitations:[strings]}.
GET /api/data → originalsyntheticfixture (customers,orders,order_lines,refunds).
POST /api/run accepts exactly {scenario:string}. IDs: october-net,october-regions,widget-net,scope-change,unknown-profit,empty-december,anchor-drift.
Response {scenario,question,baseline:{label,sql,columns,rows,status,detail?},product:{status:"answer"|"refusal"|"error",columns:[],rows:[],sql:string,parameters:string,definition_digest:string,definition_version:"demo-v1",refusal:{code,detail}|null,elapsed_ms:number,engine:"sutura0.11.0"},reference:{description:string,rows:[]},notes:[strings],live:true,llm:false}.
Knowncontrolledrefusals returned asHTTP200 applicationresult; malformed/unknownclientinput as400. Unexpectedproductfailure as502 with expliciterror. No nativeexecpaths/SQLacceptedfromclient.

Controls: october-net deliberately omitsrefundsubtraction47000vsproduct37500. october-regions usescorrectSQL14500/23000, noaccuracygainclaim. widget-net usescorrectEXISTS23500; showpreparedflaglimit. scope-change manuallyauthoredpendingquery6000vsproductundeclareddimensionrefusal. unknown-profit missingdefinition, baselineunavailableandproductmetricunknown. empty-december control0vsproduct[] (do notnormalize). anchor-drift adds1000c to preparedorder2netinTEMPcopy; baselineandproductreadthatsameprepareddata: rawSQL38500vsproductanchor37500refusal; labelcontrolleddataerror. product process may useCLIqueryandcompile instead of a persistentHTTPdaemon; stillrealengineexecution. Recordactualrefusals/digest.

Container: PythonstandardlibraryhostHTTPserver onPORT(default8080); officialSuturabinaryandNixclosurecopiedfrompinnedreleaseimage, noNPMorPipdependencies. Publicrequestexecutesallowedcatalogqueryonly, no arbitrarySQL. TwoCLIrequestsconcurrentmax, subprocess timeout20s, syntheticdatareadonly except perrequesttemporaryanchordriftcopy. Do not injectpublicAPIkeys or pretendenduserisolation.
