import { Helmet } from "react-helmet";
import { useLocation } from "react-router";

const Canonical = () => {
    const location = useLocation();

    const currentHost = window.location.host;

    if (
        currentHost === "staging.nextbus.cc" ||
        currentHost === "nextbus2.orbitix.dev"
    ) {
        return null;
    }

    const preferredDomain = "nextbus.org.uk";
    const canonicalUrl = `https://${preferredDomain}${location.pathname}${location.search}`;

    return (
        <Helmet key="canonical">
            <link rel="canonical" href={canonicalUrl} />
        </Helmet>
    );
};

export default Canonical;
